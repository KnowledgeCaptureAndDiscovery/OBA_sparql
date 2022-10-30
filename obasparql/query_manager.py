import json
import logging.config
import os
from pathlib import Path
from typing import Dict, Tuple

import validators
from pyld import jsonld
from rdflib import Graph
from obasparql.sparqlconnector import SPARQLConnector
from obasparql import gquery
from obasparql.static import *
from obasparql.utils import generate_new_id, primitives, convert_snake

EMBED_OPTION = "@always"
JSONLD = 'json-ld'
glogger = logging.getLogger("grlc")
logger = logging.getLogger('oba')


def remove_jsonld_key(tmp_context_class, key):
    """Remove json key from context

    Args:
        tmp_context_class (dict): the dict to remove the key from
        key (str): the key to remove
    """
    try:
        tmp_context_class.pop(key)
    except KeyError:
        logging.debug("The context file does not contains the id or type key")


class QueryManager:
    """Class to handle queries
    """

    def __init__(self,
                 endpoint: str,
                 named_graph_base: str,
                 uri_prefix: str,
                 queries_dir: str,
                 context_dir: str,
                 endpoint_username=None,
                 endpoint_password=None):
        """Constructor of the QueryManager class

        Args:
            endpoint (str): the endpoint server
            named_graph_base (str): the prefix or base of the name graphs
            uri_prefix (str): prefix for the URIs of new resource
            queries_dir (str): the directory where the queries are stored
            context_dir (str): the directory where the context are
            endpoint_username (str, optional): the username to access the endpoint. Defaults to None.
            endpoint_password ([type], optional): [description]. Defaults to None.

        Raises:
            e: [description]
            e: [description]
            e: [description]

        Returns:
            [type]: [description]
        """
        self.endpoint = endpoint
        self.endpoint_username = endpoint_username
        self.endpoint_password = endpoint_password
        self.update_endpoint = f'{self.endpoint}/update'
        self.query_endpoint = f'{self.endpoint}/query'
        self.named_graph_base = named_graph_base
        self.uri_prefix = uri_prefix
        self.sparql = SPARQLConnector(query_endpoint=self.endpoint,
                                      update_endpoint=self.update_endpoint,
                                      auth=(self.endpoint_username,
                                            self.endpoint_password),
                                      method="POST",
                                      returnFormat='json-ld')
        queries_dir = Path(queries_dir)
        context_dir = Path(context_dir)
        default_dir = queries_dir / DEFAULT_DIR

        # Obtain default queries
        queries = self.read_template(default_dir)
        setattr(self, "_default_", queries)

        # Overwrite default queries by class
        for owl_class in os.listdir(queries_dir):
            queries = self.read_template(queries_dir / owl_class)
            setattr(self, owl_class, self._default_)
            for key, _ in queries.items():
                k = getattr(self, owl_class)
                k[key] = queries[key]
        for query_name, query_sparql in queries.items():
            glogger.debug(query_name)
            glogger.debug(query_sparql)

        try:
            context_json = CONTEXT_FILE
            context_class_json = CONTEXT_CLASS_FILE
            temp_context = json.loads(
                self.read_context(context_dir / context_json))[CONTEXT_KEY]
            tmp_context_class = json.loads(
                self.read_context(context_dir /
                                  context_class_json))[CONTEXT_KEY]
        except FileNotFoundError as e:
            logging.error(f"{e}")
            exit(1)

        try:
            context_overwrite_json = CONTEXT_OVERWRITE_CLASS_FILE
            context_overwrite_path = context_dir / context_overwrite_json
            self.context_overwrite = json.loads(self.read_context(context_overwrite_path))[CONTEXT_KEY]
        except FileNotFoundError as e:
            self.context_overwrite = {}

        remove_jsonld_key(tmp_context_class, CONTEXT_TYPE_KEY)
        remove_jsonld_key(tmp_context_class, CONTEXT_ID_KEY)

        self.context = temp_context.copy()
        self.convert_snake_dict(temp_context)
        self.context = {CONTEXT_KEY: self.context}
        self.class_context = tmp_context_class.copy()

    def get_resource(self, **kwargs):
        """
        Handle the GET Requests
        Parameters
        ----------
        kwargs:

        Returns
        -------

        """

        request_args: Dict[str, str] = {}
        if PAGE_KEY in kwargs:
            request_args[PAGE_KEY] = kwargs[PAGE_KEY]
        if PER_PAGE_KEY in kwargs:
            request_args[PER_PAGE_KEY] = kwargs[PER_PAGE_KEY]

        if CUSTOM_QUERY_NAME in kwargs:
            return self.get_resource_custom(request_args=request_args,
                                            **kwargs)
        else:
            return self.get_resource_not_custom(request_args=request_args,
                                                **kwargs)

    def get_resource_custom(self, request_args, **kwargs):
        """
        Prepare request for custom queries
        : param request_args: contains the values to replaced in the query
        : param kwargs:
        : return:
        """
        query_type = kwargs[CUSTOM_QUERY_NAME]
        if ID_KEY in kwargs:
            return self.get_one_resource(request_args=request_args,
                                         query_type=query_type,
                                         **kwargs)
        else:
            if "label" in kwargs and kwargs["label"] is not None:
                request_args["label"] = kwargs["label"]
            return self.get_all_resource(request_args=request_args,
                                         query_type=query_type,
                                         **kwargs)

    def get_resource_not_custom(self, request_args, **kwargs):
        """
        Prepare request for not-custom queries

        : param request_args: contains the values to replaced in the query
        : param kwargs:
        : return:
        """
        if ID_KEY in kwargs and USERNAME_KEY in kwargs:
            return self.get_one_resource(request_args=request_args,
                                         query_type=QUERY_TYPE_GET_ONE_USER,
                                         **kwargs)
        elif ID_KEY in kwargs and USERNAME_KEY not in kwargs:
            return self.get_one_resource(request_args=request_args,
                                         query_type=QUERY_TYPE_GET_ONE,
                                         **kwargs)

        elif ID_KEY not in kwargs:
            # TODO: Support label search
            # if LABEL_KEY in kwargs and kwargs[LABEL_KEY] is not None:
            # logging.warning("not supported")
            if USERNAME_KEY in kwargs:
                return self.get_all_resource(
                    request_args=request_args,
                    query_type=QUERY_TYPE_GET_ALL_USER,
                    **kwargs)
            elif USERNAME_KEY not in kwargs:
                return self.get_all_resource(request_args=request_args,
                                             query_type=QUERY_TYPE_GET_ALL,
                                             **kwargs)

    def get_one_resource(self, request_args, query_type, **kwargs):
        """
        Handles a GET method to get one resource
        : param query_type: QUERY_TYPE_GET_ONE or QUERY_TYPE_GET_ONE_USER
        : param request_args:
        : param kwargs:
        : type kwargs:
        : return:
        : rtype:
        """
        owl_class_name, resource_type_uri, username = self.parse_request_arguments(
            **kwargs)
        request_args[SPARQL_ID_TYPE_VARIABLE] = self.build_instance_uri(
            kwargs[ID_KEY])
        request_args[SPARQL_GRAPH_TYPE_VARIABLE] = self.generate_graph(
            username)
        skip_id_framing = True if SKIP_ID_FRAMING_KEY in kwargs and kwargs[
            SKIP_ID_FRAMING_KEY] else False
        return self.request_one(owl_class_name, request_args,
                                resource_type_uri, query_type, skip_id_framing)

    def get_all_resource(self, request_args, query_type, **kwargs):
        """
        Handles a GET method to get all resource by rdf_type
        : param request_args: contains the values of the variables of the SPARQL query.
                             See SPARQL_QUERY_TYPE_VARIABLE and SPARQL_GRAPH_TYPE_VARIABLE
        : param query_type: QUERY_TYPE_GET_ALL or QUERY_TYPE_GET_ALL_USER
        : param kwargs:
        : type kwargs:
        : return:
        : rtype:
        """
        owl_class_name, resource_type_uri, username = self.parse_request_arguments(
            **kwargs)
        request_args[SPARQL_QUERY_TYPE_VARIABLE] = resource_type_uri
        request_args[SPARQL_GRAPH_TYPE_VARIABLE] = self.generate_graph(
            username)
        return self.request_all(owl_class_name, request_args,
                                resource_type_uri, query_type)

    # TODO: Merge request_one and request_all
    def request_one(self,
                    owl_class_name: str,
                    request_args: dict,
                    resource_type_uri: str,
                    query_type: str,
                    skip_id_framing: bool = False) -> dict:
        """Implements the request for one resource

        Args:
            owl_class_name (str): The name of the class
            request_args (dict): Contains the values of the variables of the SPARQL query.
            resource_type_uri (str): The uri of the class
            query_type (str): Indicates the type of query
            skip_id_framing (bool, optional): Request must be False Defaults to False.

        Returns:
            dict: The response of the request as JSON format
        """
        try:
            return self.obtain_query(query_directory=owl_class_name,
                                     owl_class_uri=resource_type_uri,
                                     query_type=query_type,
                                     request_args=request_args,
                                     skip_id_framing=skip_id_framing)
        except:
            logger.error("Exception occurred", exc_info=True)
            return "Bad request", 500, {}

    #TODO: the query_type is hardcoded. It should be passed as a parameter
    def request_all(self,
                    owl_class_name: str,
                    request_args: dict,
                    resource_type_uri: str,
                    query_type="get_all_user") -> dict:
        """Implements the request for resources

        Args:
            owl_class_name (str): The name of the class
            request_args (dict): Contains the values of the variables of the SPARQL query.
            resource_type_uri (str): The uri of the class
            query_type (str, optional): Indicates the query type. Defaults to "get_all_user".

        Returns:
            [type]: [description]
        """
        try:
            return self.obtain_query(query_directory=owl_class_name,
                                     owl_class_uri=resource_type_uri,
                                     query_type=query_type,
                                     request_args=request_args)
        except Exception as e:
            logger.error(e, exc_info=True)
            return "Bad request error"

    def put_resource(self, **kwargs):
        """Handle a PUT method to update a resource

        Returns:
            dict: The response of the request as JSON format
        """
        resource_uri = self.build_instance_uri(kwargs[ID_KEY])
        body = kwargs["body"].dict()
        body["id"] = resource_uri            
        try:
            username = kwargs["user"]
        except Exception:
            logger.error("Missing username", exc_info=True)
            return "Bad request: missing username"

        # DELETE QUERY
        request_args_delete: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.generate_graph(username),
            "delete_incoming_relations": False
        }

        try:
            self.delete_query(request_args_delete)
        except:
            logger.error("Exception occurred", exc_info=True)
            return "Error deleting query"

        # INSERT QUERY
        body_json = self.json_to_jsonld(body)
        prefixes, triples = self.get_insert_query(body_json)
        prefixes = '\n'.join(prefixes)
        triples = '\n'.join(triples)

        request_args: Dict[str, str] = {
            "prefixes": prefixes,
            "triples": triples,
            "g": self.generate_graph(username)
        }
        if self.insert_query(request_args=request_args):
            return body
        else:
            return "Error inserting query"

    def delete_resource(self,
                        id: str,
                        user: str,
                        rdf_type_uri: str = None,
                        rdf_type_name: str = None,
                        kls: str = None) -> dict:
        """Handle a DELETE method to delete a resource

        Args:
            id (str): the resource id
            user (str): the user who is deleting the resource
            rdf_type_uri (str, optional): The rdf type uri of the resource. Defaults to None.
            rdf_type_name (str, optional): The class name of the resource. Defaults to None.
            kls (str, optional): TODO: I don't remember. Defaults to None.

        Returns:
            dict: The response of the request as JSON format
        """
        resource_uri = self.build_instance_uri(id)
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.generate_graph(user),
            "delete_incoming_relations": True
        }
        return self.delete_query(request_args)

    def post_resource(self,
                      user,
                      body,
                      rdf_type_uri,
                      rdf_type_name=None,
                      kls=None):
        """
        Post a resource and generate the id
        Args:
            username: named graph where to do the insert
            body: JSON to insert
            rdf_type_uri: RDF Class where to insert the target instance described in body.
        """
        if body.type and rdf_type_uri is not body.type:
            body.type.append(rdf_type_uri)
        else:
            body.type = [rdf_type_uri]
        body = body.dict()
        body[ID_KEY] = generate_new_id()
        self.traverse_obj(body, user)
        insert_response = self.insert_all_resources(body, user)

        if insert_response:
            return body
        else:
            return "Error inserting resource", 407, {}

    # SPARQL AND JSON LD METHODS

    def obtain_query(self,
                     query_directory,
                     owl_class_uri,
                     query_type,
                     request_args=None,
                     skip_id_framing=False):
        """Generate the query, dispatch it to the SPARQL endpoint, frame it and return the response

        Args:
            query_directory (str): The directory where the query template is located
            owl_class_uri (str): The uri of the class 
            query_type (str): The type of query
            request_args (str, optional): The arguments of the query. Defaults to None.
            skip_id_framing (bool, optional): Indicates if the id framing must be skipped. Defaults to False.

        Raises:
            e: [description]

        Returns:
            [type]: [description]
        """
        query_template = getattr(self, query_directory)[query_type]
        if PAGE_KEY in request_args and PER_PAGE_KEY in request_args:
            request_args["offset"] = (request_args[PAGE_KEY] -
                                      1) * request_args[PER_PAGE_KEY]
        try:
            result = self.dispatch_sparql_query(
                raw_sparql_query=query_template, request_args=request_args)
        except Exception as e:
            raise e

        logger.debug("response: {}".format(result))
        try:
            if "resource" in request_args and not skip_id_framing:
                return self.frame_results(result, owl_class_uri,
                                        request_args["resource"])
            return self.frame_results(result, owl_class_uri)
        except Exception as e:
            raise e

    def overwrite_endpoint_context(self, endpoint_context: dict):
        """Overwrite the endpoint context

        Args:
            endpoint_context (dict): The endpoint context to be overwrite
        """
        for key, value in self.context_overwrite.items():
            if key in endpoint_context:
                endpoint_context[key] = value

    def frame_results(self,
                      response: str,
                      owl_class_uri: str,
                      owl_resource_iri: str = None):
        """Frame the results of the query

        Args:
            response (str): The response from the endpoint. The format is JSON-LD
            owl_class_uri (str): The uri of the class
            owl_resource_iri (str, optional): The resource uri. Defaults to None.

        Returns:
            [type]: [description]
        """
        try:
            response_dict = json.loads(response)
        except Exception:
            glogger.error("json serialize failed", exc_info=True)
            raise Exception("json serialize failed")
            
        if len(response_dict) == 0:
            #Fuseki sometimes return a json with graph and something not...
            if "@id" in response_dict and '@graph' not in response_dict:
                return []

        if '@context' in response_dict:
            response_context = response_dict['@context']
        else:
            response_context = {}

        if '@graph' in response_dict:
            response_graph = response_dict['@graph']
        else:
            response_graph = {}

        frame = {"@context": response_context, "@type": owl_class_uri}
        # if owl_resource_iri is set, the user is requesting a specific resource and we must add it to the frame
        if owl_resource_iri is not None:
            frame['@id'] = owl_resource_iri
        frame["@context"][ID_KEY] = "@id"

        # we must force that the type is a list
        frame["@context"]["type"] = {"@container": "@set", "@id": "@type"}
        # we must force that all the properties are lists
        for prop in frame["@context"].keys():
            if isinstance(frame["@context"][prop], dict):
                frame["@context"][prop]["@container"] = "@set"

        #TODO: I don't know why but the following line is needed to avoid the error:
        if 'id' in response_graph:
            del response_graph[ID_KEY]

        # Context (returned by the endpoint) does not contain information about the classes
        # so we must add it to the frame
        self.overwrite_endpoint_context(frame["@context"])
        frame["@context"] = {**self.class_context, **frame["@context"]}

        framed = jsonld.frame(
            {
                "@graph": response_graph,
                "@context": response_context
            }, frame, {"embed": (f"{EMBED_OPTION}")})

        if '@graph' in framed:
            return framed['@graph']
        else:
            if '@context' in framed:
                del framed['@context']
            return framed

    # UPDATE METHODS

    def traverse_obj(self, body, username):
        '''
        Utils method to insert nested resources
        Parameters
        ----------
        body : JSON with the resource (and nested resources) to insert
        username : named graph where to insert the resource

        Returns
        -------

        '''
        for key, value in body.items():
            if key != "openapi_types" and key != "attribute_map":
                if isinstance(value, list):
                    for inner_values in value:
                        if not (isinstance(inner_values, primitives.__args__)
                                or isinstance(inner_values, dict)):
                            list_of_obj = self.get_all_complex_objects(
                                inner_values)
                            if len(list_of_obj) != 0:
                                self.traverse_obj(inner_values, username)

                            if inner_values.id is None:
                                inner_values.id = generate_new_id()
                                self.insert_all_resources(
                                    inner_values, username)
                elif isinstance(value, dict):
                    pass

    def get_all_complex_objects(self, body: dict) -> list:
        """Get all the complex objects in a dictionary (recursive)
        A complex object is an object that has an id and a type

        Args:
            body (dict): The dictionary to be traversed

        Returns:
            list: a list of complex objects
        """
        l = []
        for key, value in body.__dict__.items():
            if key != "openapi_types" and key != "attribute_map":
                if isinstance(value, list):
                    for inner_values in value:
                        if not isinstance(inner_values,
                                          str) and not isinstance(
                                              inner_values, dict):
                            l.append(inner_values)
                elif isinstance(value, dict):
                    pass
        return l

    def json_to_jsonld(self, resource: dict) -> dict:
        """Convert a JSON to JSON-LD (recursive). Used by POST and PUT

        Args:
            resource (dict): The resource to be converted

        Returns:
            dict: The resource in JSON-LD
        """
        resource_dict = resource
        resource_dict["id"] = self.build_instance_uri(resource_dict["id"])
        resource_dict['@context'] = self.context
        resource_json = json.dumps(resource_dict)
        return resource_json

    def insert_query(self, request_args: dict) -> bool:
        """Generate the insert query

        Args:
            request_args (dict): The request arguments (from the request)

        Returns:
            bool: True if the query was generated successfully, False otherwise
        """
        query_string = f'{request_args["prefixes"]}' \
              f'INSERT DATA {{ GRAPH <{request_args["g"]}> ' \
              f'{{ {request_args["triples"]} }} }}'
        try:
            print(query_string)
            self.sparql.update(query_string)
        except Exception as err:
            glogger.error("Exception occurred", exc_info=True)
            return False
        return True

    def delete_query(self, request_args: str):
        """Delete a resource

        Args:
            request_args (str): The request arguments (from the request)

        Returns:
            [type]: A tuple (message, http_code, response)
        """
        query_string = f'' \
              f'DELETE WHERE {{ GRAPH <{request_args["g"]}> ' \
              f'{{ <{request_args["resource"]}> ?p ?o . }} }}'
        try:
            glogger.info("deleting {}".format(request_args["resource"]))
            glogger.debug("deleting: {}".format(query_string))
            self.sparql.update(query_string)
        except Exception as e:
            glogger.error("Exception occurred", exc_info=True)
            return "Error delete query"

        if request_args["delete_incoming_relations"]:
            query_string_reverse = f'' \
                    f'DELETE WHERE {{ GRAPH <{request_args["g"]}> ' \
                    f'{{ ?s ?p <{request_args["resource"]}>  }} }}'
            try:
                glogger.info("deleting incoming relations {}".format(
                    request_args["resource"]))
                glogger.debug("deleting: {}".format(query_string_reverse))
                self.sparql.update(query_string_reverse)
            except Exception as e:
                glogger.error("Exception occurred", exc_info=True)
                return "Error delete query"
        return "Deleted"

    def get_insert_query(self, resource_json: str):
        """Convert the JSON-LD to triple to be inserted"""
        prefixes = []
        triples = []
        g = Graph().parse(data=resource_json,
                          format='json-ld',
                          publicID=self.uri_prefix)
        s = g.serialize(format='turtle')
        for n in g.namespace_manager.namespaces():
            prefixes.append(f'PREFIX {n[0]}: <{n[1]}>')

        for line in s.split('\n'):
            if not line.startswith('@prefix'):
                triples.append(line)
        return prefixes, triples

    # TODO: Refactoring as a utils method. Remove self param
    def convert_snake_dict(self, temp_context: Dict):
        """
        The Python server generated by OBA uses snake_case format for the JSON key.
        This method generates the context used on the JSON-LD operations
        Parameters
        ----------
        temp_context: Temporal dictionary with the JSON-LD context

        Returns
        -------

        """

        for key, value in temp_context.items():
            key_snake = convert_snake(key)
            self.context[key] = value
            if key_snake != key:
                self.context[key_snake] = value

    # TODO: Refactoring as a utils method. Remove self param
    def generate_graph(self, username: str) -> str:
        """Generate the graph URI

        Args:
            username (str): The username

        Returns:
            str: The graph URI
        """
        return "{}{}".format(self.named_graph_base, username)

    def build_instance_uri(self, _id: str) -> str:
        """Create the instance URI from the id and the URI prefix

        Args:
            _id (str): id of the resource

        Returns:
            str: The instance URI
        """
        if validators.url(_id):
            return _id
        return f"{self.uri_prefix}{_id}"

    @staticmethod
    def read_context(context_file):
        """
        Read the context file
        : param context_file: Absolute path of the file
        : type context_file: string
        : return: Contents of the file
        : rtype: string
        """
        try:
            with open(context_file, 'r') as reader:
                return reader.read()
        except FileNotFoundError as e:
            logging.error(f"{context_file} missing")
            raise e

    @staticmethod
    def read_template(owl_class_dir):
        queries = {}
        for file_query in os.listdir(owl_class_dir):
            filename, file_extension = os.path.splitext(file_query)
            if file_extension == ".rq":
                with open(owl_class_dir / file_query, 'r') as reader:
                    key_name = filename
                    queries[key_name] = reader.read()
        return queries

    def insert_all_resources(self, body, username):
        body_json = self.json_to_jsonld(body)
        prefixes, triples = self.get_insert_query(body_json)
        prefixes = '\n'.join(prefixes)
        triples = '\n'.join(triples)
        request_args: Dict[str, str] = {
            "prefixes": prefixes,
            "triples": triples,
            "g": self.generate_graph(username)
        }
        insert_response = self.insert_query(request_args=request_args)
        return insert_response

    @staticmethod
    def parse_request_arguments(**kwargs) -> Tuple[str, str, str]:
        """Parse the request arguments into variables

        Returns:
            Tuple[str, str, str]: [description]
        """
        if USERNAME_KEY in kwargs:
            username = kwargs[USERNAME_KEY]
        else:
            username = None
        owl_class_name = kwargs["rdf_type_name"]
        resource_type_uri = kwargs["rdf_type_uri"]
        return owl_class_name, resource_type_uri, username

    def dispatch_sparql_query(self, raw_sparql_query: str, request_args: str):
        """Replace the variables in the query with the request arguments and send it

        Args:
            raw_sparql_query (str): the raw query
            request_args (str): the request arguments to be replaced

        Raises:
            e: [description]

        Returns:
            dict: JSON-LD response
        """

        query_metadata = gquery.get_metadata(raw_sparql_query, self.endpoint)
        rewritten_query = query_metadata['query']
        # Rewrite query using parameter values
        if query_metadata['type'] == 'SelectQuery' or query_metadata[
                'type'] == 'ConstructQuery':
            try:
                rewritten_query = gquery.rewrite_query(
                    query_metadata['original_query'],
                    query_metadata['parameters'], request_args)
            except Exception as e:
                logger.error("Parameters expected: {} ".format(
                    query_metadata['parameters']))
                logger.error("Parameters given: {} ".format(request_args))
                raise e
        # Rewrite query using pagination
        print(request_args)
        if PER_PAGE_KEY in request_args and "offset" in request_args:
            print("here")
            rewritten_query = rewritten_query.replace(
                "LIMIT 100", "LIMIT {}".format(request_args[PER_PAGE_KEY]))
            rewritten_query = rewritten_query.replace(
                "OFFSET 0", "OFFSET {}".format(request_args["offset"]))
        print(rewritten_query)
        logger.info(rewritten_query)
        return self.sparql.query(rewritten_query)


def merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res
