import json
import os
from pathlib import Path

from SPARQLWrapper.SPARQLExceptions import EndPointInternalError, QueryBadFormed, Unauthorized, EndPointNotFound
from pyld import jsonld
from SPARQLWrapper import SPARQLWrapper, POST, RDFXML, JSONLD
import re
import logging.config
from obasparql import gquery
EMBED_OPTION = "@always"

glogger = logging.getLogger("grlc")
logger = logging.getLogger('oba')


def convert_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class QueryManager:
    def __init__(self, **kwargs):
        """
        Load the queries template from the directory
        :param kwargs: contains the queries and context directories
        :type kwargs: dict
        """
        logger.debug("setting contexts")
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

    @staticmethod
    def insert_query(endpoint, request_args):
        query_string = f'{request_args["prefixes"]}' \
                       f'INSERT DATA {{ GRAPH <{request_args["g"]}> ' \
                       f'{{ {request_args["triples"]} }} }}'
        sparql = SPARQLWrapper(endpoint)
        sparql.setMethod(POST)
        try:
            sparql.setQuery(query_string)
            glogger.debug("insert_query: {}".format(query_string))
            sparql.query()
        except:
            glogger.error("Exception occurred", exc_info=True)
            return False
        return True

    @staticmethod
    def delete_query(endpoint, request_args):
        sparql = SPARQLWrapper(endpoint)
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

    def obtain_query(self, query_directory, owl_class_uri, query_type, endpoint, request_args=None, formData=None,
                     auth={}):
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
        """
        query_template = getattr(self, query_directory)[query_type]
        result = dispatch_sparql_query(raw_sparql_query=query_template, request_args=request_args,
                                       endpoint=endpoint, return_format=JSONLD, auth=auth)
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
            owl_resource_iri:
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


def dispatch_sparql_query(raw_sparql_query, request_args, endpoint, return_format, auth={}):
    query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)
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
    if query_metadata['type'] == 'SelectQuery' and 'pagination' in query_metadata:
        try:
            rewritten_query = gquery.paginate_query(rewritten_query, query_metadata['pagination'], request_args)
        except Exception as e:
            logger.error("Parameters expected: {} ".format(query_metadata['parameters']))
            logger.error("Parameters given: {} ".format(request_args))
            raise e

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(rewritten_query)
    sparql.setReturnFormat(return_format)
    try:
        results = sparql.query().convert().serialize(format=return_format)
    except EndPointInternalError as e:
        logger.error(e, exc_info=True)
    except EndPointInternalError as e:
        logger.error(e, exc_info=True)
    except QueryBadFormed as e:
        logger.error(e, exc_info=True)
    except Unauthorized as e:
        logger.error(e, exc_info=True)
    except EndPointNotFound as e:
        logger.error(e, exc_info=True)
    return results
