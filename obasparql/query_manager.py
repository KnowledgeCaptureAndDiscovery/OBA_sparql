import json
import logging.config
import os
import re
from pathlib import Path
from typing import Dict

from SPARQLWrapper import SPARQLWrapper, POST, JSONLD, DIGEST
from SPARQLWrapper.SPARQLExceptions import EndPointInternalError, QueryBadFormed, Unauthorized, EndPointNotFound
from pyld import jsonld
from rdflib import Graph

from obasparql import gquery
from obasparql.utils import generate_new_uri, primitives

EMBED_OPTION = "@always"

glogger = logging.getLogger("grlc")
logger = logging.getLogger('oba')


def convert_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class QueryManager:
    def __init__(self, endpoint, graph_base, prefix, endpoint_username=None, endpoint_password=None, **kwargs):
        """
        Load the queries template from the directory
        :param kwargs: contains the queries and context directories
        :type kwargs: dict
        """
        self.endpoint = endpoint
        self.endpoint_username = endpoint_username
        self.endpoint_password = endpoint_password
        self.update_endpoint = f'{self.endpoint}/update'
        self.query_endpoint = f'{self.endpoint}/query'
        self.graph_base = graph_base
        self.prefix = prefix
        self.kwargs = kwargs
        queries_dir = Path(kwargs["queries_dir"])
        context_dir = Path(kwargs["context_dir"])
        default_dir = queries_dir / "_default_"

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
        # Fix: oba needs key as camelcase and snake_case
        temp_context = json.loads(self.read_context(context_dir / "context.json"))["@context"]
        self.context = temp_context.copy()
        for key, value in temp_context.items():
            key_snake = convert_snake(key)
            self.context[key] = value
            if key_snake != key:
                self.context[key_snake] = value
        self.context = {"@context": self.context}

    def get_resource(self, **kwargs):
        """
        This method handles a GET METHOD
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        # args
        request_args: Dict[str, str] = {}

        if "custom_query_name" in kwargs:
            query_type = kwargs["custom_query_name"]
            return self.get_resource_custom(request_args=request_args, query_type=query_type, **kwargs)
        else:
            return self.get_resource_not_custom(request_args=request_args, **kwargs)

    def get_resource_custom(self, query_type, request_args, **kwargs):
        """
        Prepare request for custom queries
        :param query_type:
        :param request_args: contains the values to replaced in the query
        :param kwargs:
        :return:
        """
        if "id" in kwargs:
            return self.get_one_resource(request_args=request_args, query_type=query_type, **kwargs)
        else:

            if "label" in kwargs and kwargs["label"] is not None:
                query_text = kwargs["label"]
                request_args["label"] = query_text
            return self.get_all_resource(request_args=request_args, query_type=query_type, **kwargs)

    def get_resource_not_custom(self, request_args, **kwargs):
        """
        Prepare request for not-custom queries

        :param request_args: contains the values to replaced in the query
        :param kwargs:
        :return:
        """
        if "id" in kwargs:
            return self.get_one_resource(request_args=request_args, query_type="get_one_user", **kwargs)

        else:
            query_type = "get_all_user"
            if "label" in kwargs and kwargs["label"] is not None:
                query_text = kwargs["label"]
                query_type = "get_all_search_user"
                request_args["text"] = query_text
            return self.get_all_resource(request_args=request_args, query_type=query_type, **kwargs)

    def get_one_resource(self, request_args, query_type="get_one_user", **kwargs):
        """
        Handles a GET method to get one resource
        :param query_type:
        :param request_args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        kls, owl_class_name, resource_type_uri, username = self.set_up(**kwargs)
        request_args["resource"] = self.build_instance_uri(kwargs["id"])
        request_args["g"] = self.generate_graph(username)
        return self.request_one(kls, owl_class_name, request_args, resource_type_uri, query_type)

    def get_all_resource(self, request_args, query_type, **kwargs):
        """
        Handles a GET method to get all resource by rdf_type
        :param request_args:
        :param query_type:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        kls, owl_class_name, resource_type_uri, username = self.set_up(**kwargs)
        request_args["type"] = resource_type_uri
        request_args["g"] = self.generate_graph(username)
        return self.request_all(kls, owl_class_name, request_args, resource_type_uri, query_type)

    def request_one(self, kls, owl_class_name, request_args, resource_type_uri, query_type="get_one_user"):
        try:
            response = self.obtain_query(query_directory=owl_class_name, owl_class_uri=resource_type_uri,
                                         query_type=query_type, request_args=request_args)
            if len(response) > 0:
                return kls.from_dict(response[0])
            else:
                return "Not found", 404, {}

        except:
            logger.error("Exception occurred", exc_info=True)
            return "Bad request", 400, {}

    def request_all(self, kls, owl_class_name, request_args, resource_type_uri, query_type="get_all_user"):
        try:
            response = self.obtain_query(query_directory=owl_class_name, owl_class_uri=resource_type_uri,
                                         query_type=query_type, request_args=request_args)
            items = []
            for d in response:
                items.append(kls.from_dict(d))
            return items
        except:
            logger.error("Exception occurred", exc_info=True)
            return "Bad request", 400, {}

    def put_resource(self, **kwargs):
        resource_uri = self.build_instance_uri(kwargs["id"])
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
        if self.insert_query(self.update_endpoint, request_args=request_args):
            return body, 201, {}
        else:
            return "Error inserting query", 407, {}

    def delete_resource(self, **kwargs):
        resource_uri = self.build_instance_uri(kwargs["id"])
        try:
            username = kwargs["user"]
        except Exception:
            logger.error("Missing username", exc_info=True)
            return "Bad request: missing username", 400, {}

        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.generate_graph(username),
            "delete_incoming_relations": True
        }
        return self.delete_query(request_args)

    def post_resource(self, **kwargs):
        """
        Post a resource and generate the id
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        body = kwargs["body"]
        rdf_type_uri = kwargs["rdf_type_uri"]
        if body.type and rdf_type_uri is not body.type:
            body.type.append(rdf_type_uri)
        else:
            body.type = [rdf_type_uri]
        body.id = generate_new_uri()
        logger.info("Inserting the resource: {}".format(body.id))

        try:
            username = kwargs["user"]

        except Exception as e:
            logger.error("Missing username", exc_info=True)
            return "Bad request: missing username", 400, {}
        self.traverse_obj(body, username)

        insert_response = self.insert_all_resources(body, username)

        if insert_response:
            return body, 201, {}
        else:
            return "Error inserting query", 407, {}

    def convert_json_to_triples(self, body):
        body_json = self.prepare_jsonld(body)
        prefixes, triples = self.get_insert_query(body_json)
        prefixes = '\n'.join(prefixes)
        triples = '\n'.join(triples)
        return prefixes, triples

    def traverse_obj(self, body, username):
        for key, value in body.__dict__.items():
            if key != "openapi_types" and key != "attribute_map":
                if isinstance(value, list):
                    for inner_values in value:
                        if not (isinstance(inner_values, primitives.__args__) or isinstance(inner_values, dict)):
                            list_of_obj = self.get_all_complex_objects(inner_values, username)
                            if len(list_of_obj) != 0:
                                self.traverse_obj(inner_values, username)

                            if inner_values.id == None:
                                inner_values.id = generate_new_uri()
                                self.insert_all_resources(inner_values, username)
                elif isinstance(value, dict):
                    pass

    def generate_graph(self, username):
        return "{}{}".format(self.graph_base, username)

    def build_instance_uri(self, uri, validators=None):
        if validators.url(uri):
            return uri
        return "{}{}".format(self.prefix, uri)

    def convert_json_to_triples(self, body):
        body_json = self.prepare_jsonld(body)
        prefixes, triples = self.get_insert_query(body_json)
        prefixes = '\n'.join(prefixes)
        triples = '\n'.join(triples)
        return prefixes, triples

    def prepare_jsonld(self, resource):
        resource_dict = resource.to_dict()
        resource_dict["id"] = self.build_instance_uri(resource_dict["id"])
        resource_dict['@context'] = self.context
        resource_json = json.dumps(resource_dict)
        return resource_json

    def insert_query(self, request_args):
        query_string = f'{request_args["prefixes"]}' \
                       f'INSERT DATA {{ GRAPH <{request_args["g"]}> ' \
                       f'{{ {request_args["triples"]} }} }}'
        sparql = SPARQLWrapper(self.update_endpoint)
        self.set_authetication(sparql)
        sparql.setMethod(POST)
        try:
            sparql.setQuery(query_string)
            glogger.debug("insert_query: {}".format(query_string))
            sparql.query()
        except:
            glogger.error("Exception occurred", exc_info=True)
            return False
        return True

    def set_authetication(self, sparql):
        sparql.setHTTPAuth(DIGEST)
        if self.endpoint_username and self.endpoint_password:
            sparql.setCredentials(self.endpoint_username, self.endpoint_password)

    def delete_query(self, request_args):
        sparql = SPARQLWrapper(self.update_endpoint)
        self.set_authetication(sparql)
        sparql.setMethod(POST)
        query_string = f'' \
                       f'DELETE WHERE {{ GRAPH <{request_args["g"]}> ' \
                       f'{{ <{request_args["resource"]}> ?p ?o . }} }}'

        try:
            glogger.info("deleting {}".format(request_args["resource"]))
            glogger.debug("deleting: {}".format(query_string))
            sparql.setQuery(query_string)
            sparql.query()
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
                sparql.setQuery(query_string_reverse)
                sparql.query()
            except Exception as e:
                glogger.error("Exception occurred", exc_info=True)
                return "Error delete query", 405, {}

        return "Deleted", 202, {}

    def get_insert_query(self, resource_json):
        prefixes = []
        triples = []
        g = Graph().parse(data=resource_json, format='json-ld', publicID=self.prefix)
        s = g.serialize(format='turtle')
        for n in g.namespace_manager.namespaces():
            prefixes.append(f'PREFIX {n[0]}: <{n[1]}>')

        for line in s.decode().split('\n'):
            if not line.startswith('@prefix'):
                triples.append(line)
        return prefixes, triples

    def get_all_complex_objects(self, body, username):
        l = []
        for key, value in body.__dict__.items():
            if key != "openapi_types" and key != "attribute_map":
                if isinstance(value, list):
                    # print(type(value[0]))
                    for inner_values in value:
                        if not isinstance(inner_values, str) and not isinstance(inner_values, dict):
                            l.append(inner_values)
                elif isinstance(value, dict):
                    pass
        return l

    def obtain_query(self, query_directory, owl_class_uri, query_type, request_args=None, auth={}):
        """
        Given the owl_class and query_type, load the query template.
        Execute the query on the remote endpoint.
        :param formData:
        :type formData:
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

        Args:
            auth ():
            owl_class_uri ():
        """
        query_template = getattr(self, query_directory)[query_type]
        if "page" in request_args and "per_page" in request_args:
            request_args["offset"] = (request_args["page"] - 1) * request_args["per_page"]
        try:
            result = self.dispatch_sparql_query(raw_sparql_query=query_template,
                                                request_args=request_args,
                                                return_format=JSONLD)
        except Exception as e:
            raise e
        logger.debug("response: {}".format(result))
        if "resource" in request_args:
            return self.frame_results(result, owl_class_uri, request_args["resource"])
        return self.frame_results(result, owl_class_uri)

    def frame_results(self, resp, owl_class_uri, owl_resource_iri=None):
        """
        Generate the framed using the owl_class.
        Frame the response and returns it.
        :param resp: JSON response from SPARQL
        :type resp: string
        :param owl_class_uri: OWL class uri
        :type owl_class: string
        :return: Framed JSON
        :rtype: string

        Args:
            owl_resource_iri ():
        """
        try:
            triples = json.loads(resp)
        except Exception:
            glogger.error("json serialize failed", exc_info=True)
            return []
        frame = self.context.copy()
        frame['@type'] = owl_class_uri
        results = {"@graph": triples, "context": self.context.copy()}

        if owl_resource_iri is not None:
            frame['@id'] = owl_resource_iri

        framed = jsonld.frame(results, frame, {"embed": ("%s" % EMBED_OPTION)})
        if '@graph' in framed:
            return framed['@graph']
        else:
            return []

    @staticmethod
    def read_context(context_file):
        """
        Read the context file
        :param context_file: Absolute path of the file
        :type context_file: string
        :return: Contents of the file
        :rtype: string
        """
        with open(context_file, 'r') as reader:
            return reader.read()

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
        if "username" in kwargs:
            username = kwargs["username"]
        else:
            username = None
        owl_class_name = kwargs["rdf_type_name"]
        resource_type_uri = kwargs["rdf_type_uri"]
        kls = kwargs["kls"]
        return kls, owl_class_name, resource_type_uri, username

    def dispatch_sparql_query(self, raw_sparql_query, request_args, return_format):
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
        if "per_page" in request_args and "offset" in request_args:
            rewritten_query = rewritten_query.replace("LIMIT 100", "LIMIT {}".format(request_args["per_page"]))
            rewritten_query = rewritten_query.replace("OFFSET 0", "OFFSET {}".format(request_args["offset"]))

        sparql = SPARQLWrapper(self.endpoint)
        sparql.setQuery(rewritten_query)
        sparql.setReturnFormat(return_format)
        try:
            return sparql.query().convert().serialize(format=return_format)
        except EndPointInternalError as e:
            logger.error(e, exc_info=True)
        except QueryBadFormed as e:
            logger.error(e, exc_info=True)
        except Unauthorized as e:
            logger.error(e, exc_info=True)
        except EndPointNotFound as e:
            logger.error(e, exc_info=True)
        raise Exception
