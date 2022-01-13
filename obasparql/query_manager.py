import json
import logging.config
import os
from pathlib import Path
from typing import Dict

import validators
from pyld import jsonld
from rdflib import Graph
from rdflib.plugins.stores.sparqlconnector import SPARQLConnector
from obasparql import gquery
from obasparql.static import *
from obasparql.utils import generate_new_id, primitives, convert_snake

EMBED_OPTION = "@always"
JSONLD = 'json-ld'
glogger = logging.getLogger("grlc")
logger = logging.getLogger('oba')


def remove_jsonld_key(tmp_context_class, key):
    try:
        tmp_context_class.pop(key)
    except KeyError:
        logging.debug(f"The context file does not contains the id or type key")


class QueryManager:
    def __init__(self,
                 endpoint,
                 named_graph_base,
                 uri_prefix,
                 queries_dir,
                 context_dir,
                 endpoint_username=None,
                 endpoint_password=None):
        """
        Parameters
        ----------
        endpoint : URL of endpoint
        named_graph_base : The prefix or base of the graphs
        uri_prefix : The prefix for the IRIs of new resource
        endpoint_username : Username of endpoint (https://github.com/RDFLib/sparqlwrapper)
        endpoint_password : Password of endpoint (https://github.com/RDFLib/sparqlwrapper)
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
                                 method="POST"
                                 )
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
            for key, value in queries.items():
                k = getattr(self, owl_class)
                k[key] = queries[key]
        for query_name, query_sparql in queries.items():
            glogger.debug(query_name)
            glogger.debug(query_sparql)

        try:
            context_json = CONTEXT_FILE
            context_class_json = CONTEXT_CLASS_FILE
            temp_context = json.loads(self.read_context(context_dir / context_json))[CONTEXT_KEY]
            tmp_context_class = json.loads(self.read_context(
                context_dir / context_class_json))[CONTEXT_KEY]
        except FileNotFoundError as e:
            logging.error(f"{e}")
            exit(1)

        try:
            context_overwrite_json = CONTEXT_OVERWRITE_CLASS_FILE
            self.context_overwrite = json.loads(self.read_context(
                context_dir / context_overwrite_json))[CONTEXT_KEY]
        except FileNotFoundError as e:
            self.context_overwrite = None

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
        kwargs :

        Returns
        -------

        """

        request_args: Dict[str, str] = {}
        if PAGE_KEY in kwargs:
            request_args[PAGE_KEY] = kwargs[PAGE_KEY]
        if PER_PAGE_KEY in kwargs:
            request_args[PER_PAGE_KEY] = kwargs[PER_PAGE_KEY]

        if CUSTOM_QUERY_NAME in kwargs:
            return self.get_resource_custom(request_args=request_args, **kwargs)
        else:
            return self.get_resource_not_custom(request_args=request_args, **kwargs)

    def get_resource_custom(self, request_args, **kwargs):
        """
        Prepare request for custom queries
        :param request_args: contains the values to replaced in the query
        :param kwargs:
        :return:
        """
        query_type = kwargs[CUSTOM_QUERY_NAME]
        if ID_KEY in kwargs:
            return self.get_one_resource(request_args=request_args, query_type=query_type, **kwargs)
        else:
            return self.get_all_resource(request_args=request_args, query_type=query_type, **kwargs)

    def get_resource_not_custom(self, request_args, **kwargs):
        """
        Prepare request for not-custom queries

        :param request_args: contains the values to replaced in the query
        :param kwargs:
        :return:
        """
        if ID_KEY in kwargs and USERNAME_KEY in kwargs:
            return self.get_one_resource(request_args=request_args, query_type=QUERY_TYPE_GET_ONE_USER, **kwargs)
        elif ID_KEY in kwargs and USERNAME_KEY not in kwargs:
            return self.get_one_resource(request_args=request_args, query_type=QUERY_TYPE_GET_ONE, **kwargs)

        elif ID_KEY not in kwargs:
            # TODO: Support label search
            # if LABEL_KEY in kwargs and kwargs[LABEL_KEY] is not None:
            # logging.warning("not supported")
            if USERNAME_KEY in kwargs:
                return self.get_all_resource(request_args=request_args, query_type=QUERY_TYPE_GET_ALL_USER, **kwargs)
            elif USERNAME_KEY not in kwargs:
                return self.get_all_resource(request_args=request_args, query_type=QUERY_TYPE_GET_ALL, **kwargs)

    def get_one_resource(self, request_args, query_type, **kwargs):
        """
        Handles a GET method to get one resource
        :param query_type: QUERY_TYPE_GET_ONE or QUERY_TYPE_GET_ONE_USER
        :param request_args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        owl_class_name, resource_type_uri, username = self.set_up(**kwargs)
        request_args[SPARQL_ID_TYPE_VARIABLE] = self.build_instance_uri(kwargs[ID_KEY])
        request_args[SPARQL_GRAPH_TYPE_VARIABLE] = self.generate_graph(username)
        skip_id_framing = True if SKIP_ID_FRAMING_KEY in kwargs and kwargs[SKIP_ID_FRAMING_KEY] else False
        return self.request_one(owl_class_name, request_args, resource_type_uri, query_type, skip_id_framing)

    def get_all_resource(self, request_args, query_type, **kwargs):
        """
        Handles a GET method to get all resource by rdf_type
        :param request_args: contains the values of the variables of the SPARQL query.
                             See SPARQL_QUERY_TYPE_VARIABLE and SPARQL_GRAPH_TYPE_VARIABLE
        :param query_type: QUERY_TYPE_GET_ALL or QUERY_TYPE_GET_ALL_USER
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        owl_class_name, resource_type_uri, username = self.set_up(**kwargs)
        request_args[SPARQL_QUERY_TYPE_VARIABLE] = resource_type_uri
        request_args[SPARQL_GRAPH_TYPE_VARIABLE] = self.generate_graph(username)
        return self.request_all(owl_class_name, request_args, resource_type_uri, query_type)

    # TODO: Merge request_one and request_all
    def request_one(self, owl_class_name, request_args, resource_type_uri, query_type, skip_id_framing=False):
        try:
            return self.obtain_query(query_directory=owl_class_name,
                                     owl_class_uri=resource_type_uri,
                                     query_type=query_type,
                                     request_args=request_args,
                                     skip_id_framing=skip_id_framing)
        except:
            logger.error("Exception occurred", exc_info=True)
            return "Bad request", 500, {}

    def request_all(self, owl_class_name, request_args, resource_type_uri, query_type="get_all_user"):
        try:
            return self.obtain_query(query_directory=owl_class_name,
                                     owl_class_uri=resource_type_uri,
                                     query_type=query_type,
                                     request_args=request_args)
        except Exception as e:
            logger.error(e, exc_info=True)
            return "Bad request error", 500, {}

    def put_resource(self, **kwargs):
        resource_uri = self.build_instance_uri(kwargs[ID_KEY])
        body = kwargs["body"]
        body.id = resource_uri

        try:
            username = kwargs["user"]
        except Exception:
            logger.error("Missing username", exc_info=True)
            return "Bad request: missing username", 400, {}

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
            return "Error deleting query", 407, {}

        # INSERT QUERY
        body_json = self.prepare_jsonld(body)
        prefixes, triples = self.get_insert_query(body_json)
        prefixes = '\n'.join(prefixes)
        triples = '\n'.join(triples)

        request_args: Dict[str, str] = {
            "prefixes": prefixes,
            "triples": triples,
            "g": self.generate_graph(username)
        }
        if self.insert_query(request_args=request_args):
            return body, 201, {}
        else:
            return "Error inserting query", 407, {}

    def delete_resource(self, username, resource_id):
        resource_uri = resource_id
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.generate_graph(username),
            "delete_incoming_relations": True
        }
        return self.delete_query(request_args)

    def post_resource(self, username, body, rdf_type_uri):
        """
        Post a resource and generate the id
        Args:
            username: named graph where to do the insert
            body: JSON to insert
            rdf_type_uri: RDF Class where to insert the target instance described in body.
        """
        if "type" in body and rdf_type_uri not in body["type"]:
            body["type"].append(rdf_type_uri)
        else:
            body["type"] = [rdf_type_uri]
        if "id" in body:
            # At the moment users cannot insert their own ids (except in complex resources).
            # If we plan to support this, we would have to check the id does not exist.
            logger.error("Resource already has an id")
            return "Error inserting resource", 407, {}
        body["id"] = generate_new_id()
        logger.info("Inserting the resource: {}".format(body["id"]))

        self.traverse_obj(body, username)

        insert_response = self.insert_all_resources(body, username)

        if insert_response:
            return body, 201, {}
        else:
            return "Error inserting resource", 407, {}

    # SPARQL AND JSON LD METHODS

    def obtain_query(self, query_directory, owl_class_uri, query_type, request_args=None, auth={},
                     skip_id_framing=False):
        """"""
        """
        Given the owl_class and query_type, load the query template.
        Execute the query on the remote endpoint.
        :param query_directory:
        :type query_directory:
        :param query_type: The type of query. Required to load the query template.
        :type query_type: string
        :param endpoint: The url of the SPARQL endpoint
        :type endpoint: string
        :param request_args:
        :type request_args:
        :return: Framed JSON
        :rtype: string
        """
        query_template = getattr(self, query_directory)[query_type]
        if PAGE_KEY in request_args and PER_PAGE_KEY in request_args:
            request_args["offset"] = (request_args[PAGE_KEY] - 1) * request_args[PER_PAGE_KEY]
        try:
            result = self.dispatch_sparql_query(raw_sparql_query=query_template,
                                                request_args=request_args,
                                                return_format=JSONLD)
        except Exception as e:
            raise e

        logger.debug("response: {}".format(result))
        if "resource" in request_args and not skip_id_framing:
            return self.frame_results(result, owl_class_uri, request_args["resource"])
        return self.frame_results(result, owl_class_uri)

    def overwrite_endpoint_context(self, endpoint_context):
        for key, value in self.context_overwrite.items():
            if key in endpoint_context:
                endpoint_context[key] = value

    def frame_results(self, resp, owl_class_uri, owl_resource_iri=None):
        try:
            response_ld_with_context = json.loads(resp)
        except Exception:
            glogger.error("json serialize failed", exc_info=True)
            return []
        if len(response_ld_with_context) == 0:
            """
            Fuseki sometimes return a json with graph and something not...
            """
            if "@id" in response_ld_with_context and '@graph' not in response_ld_with_context:
                return []

        new_context = self.context['@context']
        new_response = {"@graph": jsonld.expand(response_ld_with_context),
                        "@context": new_context}
        frame = {"@context": new_context, "@type": owl_class_uri}

        if owl_resource_iri is not None:
            frame['@id'] = owl_resource_iri
        frame["@context"]["type"] = "@type"
        frame["@context"][ID_KEY] = "@id"
        for prop in frame["@context"].keys():
            if isinstance(frame["@context"][prop], dict):
                frame["@context"][prop]["@container"] = "@set"
                if "@type" in frame["@context"][prop] and frame["@context"][prop]['@type'] != "@id":
                    frame["@context"][prop].pop("@type")
        if '@graph' in response_ld_with_context and 'id' in response_ld_with_context["@graph"]:
            del response_ld_with_context["@graph"][ID_KEY]

        if '@graph' in response_ld_with_context:
            logger.debug(json.dumps(response_ld_with_context["@graph"], indent=4))
        framed = jsonld.frame(new_response, frame, {"embed": ("%s" % EMBED_OPTION)})
        if '@graph' in framed:
            return framed['@graph']
        else:
            return []

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
            # if key != "openapi_types" and key != "attribute_map": #not needed
            if isinstance(value, list):
                for inner_values in value:
                    # if not (isinstance(inner_values, primitives.__args__) or isinstance(inner_values, dict)):
                    if not (isinstance(inner_values, primitives.__args__)):
                        self.process_dictionary(inner_values, username)
            elif isinstance(value, dict):
                self.process_dictionary(value, username)

    def process_dictionary(self, dictionary, username):
        list_of_obj = self.get_all_complex_objects(dictionary, username)
        if len(list_of_obj) != 0:
            self.traverse_obj(dictionary, username)
        if "id" not in dictionary:
            dictionary["id"] = generate_new_id()
            self.insert_all_resources(dictionary, username)

    def get_all_complex_objects(self, body, username):
        l = []
        for key, value in body.items():
            # if key != "openapi_types" and key != "attribute_map": #not needed
            if isinstance(value, list):
                for inner_values in value:
                    if not isinstance(inner_values, str):
                        l.append(inner_values)
            elif isinstance(value, dict):
                l.append(value)
        return l

    def prepare_jsonld(self, resource):
        if not isinstance(resource, Dict):
            resource_dict = resource.to_dict()
        else:
            resource_dict = resource.copy()
            # we return the id as a URI as part of the body
            resource[ID_KEY] = resource_dict[ID_KEY] = self.build_instance_uri(
                resource_dict[ID_KEY])
        resource_dict[ID_KEY] = resource[ID_KEY]
        resource_dict['@context'] = self.context["@context"]
        resource_json = json.dumps(resource_dict, default=str)
        return resource_json

    def insert_query(self, request_args):
        query_string = f'{request_args["prefixes"]}' \
                       f'INSERT DATA {{ GRAPH <{request_args["g"]}> ' \
                       f'{{ {request_args["triples"]} }} }}'


        try:
            self.sparql.update(query_string)
        except Exception as err:
            glogger.error("Exception occurred", exc_info=True)
            return False
        return True

    def delete_query(self, request_args):
        query_string = f'' \
                       f'DELETE WHERE {{ GRAPH <{request_args["g"]}> ' \
                       f'{{ <{request_args["resource"]}> ?p ?o . }} }}'
        try:
            glogger.info("deleting {}".format(request_args["resource"]))
            glogger.debug("deleting: {}".format(query_string))
            self.sparql.query(query_string)
        except Exception as e:
            glogger.error("Exception occurred", exc_info=True)
            return "Error delete query", 405, {}

        if request_args["delete_incoming_relations"]:
            query_string_reverse = f'' \
                                   f'DELETE WHERE {{ GRAPH <{request_args["g"]}> ' \
                                   f'{{ ?s ?p <{request_args["resource"]}>  }} }}'
            try:
                glogger.info("deleting incoming relations {}".format(request_args["resource"]))
                glogger.debug("deleting: {}".format(query_string_reverse))
                self.sparql.query(query_string_reverse)
            except Exception as e:
                glogger.error("Exception occurred", exc_info=True)
                return "Error delete query", 405, {}
        return "Deleted", 202, {}

    def get_insert_query(self, resource_json):
        prefixes = []
        triples = []
        g = Graph().parse(data=resource_json, format='json-ld', publicID=self.uri_prefix)
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
        temp_context : Temporal dictionary with the JSON-LD context

        Returns
        -------

        """

        for key, value in temp_context.items():
            key_snake = convert_snake(key)
            self.context[key] = value
            if key_snake != key:
                self.context[key_snake] = value

    # TODO: Refactoring as a utils method. Remove self param
    def generate_graph(self, username):
        return "{}{}".format(self.named_graph_base, username)

    # TODO: Refactoring as a utils method. Remove self param
    def build_instance_uri(self, uri):
        if validators.url(uri):
            return uri
        return "{}{}".format(self.uri_prefix, uri)

    @staticmethod
    def read_context(context_file):
        """
        Read the context file
        :param context_file: Absolute path of the file
        :type context_file: string
        :return: Contents of the file
        :rtype: string
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
        body_json = self.prepare_jsonld(body)
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
    def set_up(**kwargs):
        if USERNAME_KEY in kwargs:
            username = kwargs[USERNAME_KEY]
        else:
            username = None
        owl_class_name = kwargs["rdf_type_name"]
        resource_type_uri = kwargs["rdf_type_uri"]
        return owl_class_name, resource_type_uri, username

    def dispatch_sparql_query(self, raw_sparql_query, request_args, return_format=JSONLD):
        query_metadata = gquery.get_metadata(raw_sparql_query, self.endpoint)
        rewritten_query = query_metadata['query']
        # Rewrite query using parameter values
        if query_metadata['type'] == 'SelectQuery' or query_metadata['type'] == 'ConstructQuery':
            try:
                rewritten_query = gquery.rewrite_query(query_metadata['original_query'], query_metadata['parameters'],
                                                       request_args)
            except Exception as e:
                logger.error("Parameters expected: {} ".format(query_metadata['parameters']))
                logger.error("Parameters given: {} ".format(request_args))
                raise e
        # Rewrite query using pagination
        if PER_PAGE_KEY in request_args and "offset" in request_args:
            rewritten_query = rewritten_query.replace(
                "LIMIT 100", "LIMIT {}".format(request_args[PER_PAGE_KEY]))
            rewritten_query = rewritten_query.replace(
                "OFFSET 0", "OFFSET {}".format(request_args["offset"]))
        logger.info(rewritten_query)

        sparql = SPARQLConnector(self.endpoint)
        response = sparql.query(rewritten_query)
        result = response.serialize(format="json-ld")
        return result
        # try:
        #     return sparql.query().response.read()
        # except EndPointInternalError as e:
        #     logger.error(e, exc_info=True)
        # except QueryBadFormed as e:
        #     logger.error(e, exc_info=True)
        # except Unauthorized as e:
        #     logger.error(e, exc_info=True)
        # except EndPointNotFound as e:
        #     logger.error(e, exc_info=True)
        # raise Exception


def merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res
