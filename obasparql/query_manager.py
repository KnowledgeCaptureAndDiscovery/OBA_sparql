import json
import os
import logging
from pathlib import Path

import requests
from pyld import jsonld
from rdflib import Graph
from grlc import gquery
from SPARQLWrapper import SPARQLWrapper, POST
import re

from .static import mime_types

glogger = logging.getLogger(__name__)
glogger.setLevel(logging.DEBUG)




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

        # Fix: oba needs key as camelcase and snake_case
        temp_context = json.loads(self.read_context(context_dir / "context.json"))["@context"]
        self.context = temp_context.copy()
        for key, value in temp_context.items():
            key_snake = convert_snake(key)
            self.context[key] = value
            if key_snake != key:
                self.context[key_snake] = value
        self.context = {"@context": self.context}
        glogger.debug(self.context)

    @staticmethod
    def insert_query(endpoint, request_args):
        query_string = f'{request_args["prefixes"]}  ' \
            f'INSERT DATA {{ GRAPH <{request_args["g"]}> ' \
            f'{{ {request_args["triples"]} }} }}'
        sparql = SPARQLWrapper(endpoint)
        sparql.setMethod(POST)
        try:
            sparql.setQuery(query_string)
            glogger.debug("insert_query: {}".format(query_string))
        except:
            glogger.error("Exception occurred", exc_info=True)
            return False
        return True

    @staticmethod
    def delete_query(endpoint, request_args):
        query_string = f'DELETE WHERE {{ GRAPH <{request_args["g"]}> ' \
            f'{{ <{request_args["resource"]}> ?p ?o . }} }}'
        sparql = SPARQLWrapper(endpoint)
        sparql.setMethod(POST)
        try:
            sparql.setQuery(query_string)
            glogger.info("deleting {}".format(request_args["resource"]))
            glogger.debug("deleting: {}".format(query_string))
        except Exception as e:
            glogger.error("Exception occurred", exc_info=True)
            return "Error delete query", 405, {}
        return "Deleted", 202, {}

    def obtain_query(self, owl_class_name, owl_class_uri, query_type, endpoint, request_args=None, formData=None, auth={}):
        """
        Given the owl_class and query_type, load the query template.
        Execute the query on the remote endpoint.
        :param formData:
        :type formData:
        :param owl_class_name:
        :type owl_class_name:
        :param query_type: The type of query. Required to load the query template.
        :type query_type: string
        :param endpoint: The url of the SPARQL endpoint
        :type endpoint: string
        :param request_args:
        :type request_args:
        :return: Framed JSON
        :rtype: string
        """
        query_template = getattr(self, owl_class_name)[query_type]
        resp, status, headers = dispatchSPARQLQuery(raw_sparql_query=query_template,
                                                    loader=None,
                                                    requestArgs=request_args,
                                                    acceptHeader="application/ld+json",
                                                    content=None,
                                                    formData=None,
                                                    requestUrl=None,
                                                    endpoint=endpoint,
                                                    auth=auth)
        glogger.debug("response: {}".format(resp))
        return self.frame_results(resp, owl_class_uri)

    def frame_results(self, resp, owl_class_uri):
        """
        Generate the framed using the owl_class.
        Frame the response and returns it.
        :param resp: JSON response from SPARQL
        :type resp: string
        :param owl_class_uri: OWL class uri
        :type owl_class: string
        :return: Framed JSON
        :rtype: string
        """
        try:
            triples = json.loads(resp)
        except Exception:
            glogger.error("json serialize failed", exc_info=True)
            return []
        glogger.debug(triples)
        frame = self.context.copy()
        frame['@type'] = owl_class_uri
        triples['@context'] = self.context.copy()
        framed = jsonld.frame(triples, frame)
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


def dispatchSPARQLQuery(raw_sparql_query, loader, requestArgs, acceptHeader, content, formData, requestUrl,
                        endpoint, auth={}):
    if not endpoint:
        endpoint, auth = gquery.guess_endpoint_uri(raw_sparql_query, loader)
        if endpoint == '':
            return 'No SPARQL endpoint indicated', 407, {}

    glogger.debug("=====================================================")
    glogger.debug("Sending query to SPARQL endpoint: {}".format(endpoint))
    glogger.debug("=====================================================")

    query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)

    acceptHeader = 'application/json' if isinstance(raw_sparql_query, dict) else acceptHeader
    pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

    rewritten_query = query_metadata['query']

    # Rewrite query using parameter values
    if query_metadata['type'] == 'SelectQuery' or query_metadata['type'] == 'ConstructQuery':
        rewritten_query = gquery.rewrite_query(query_metadata['original_query'], query_metadata['parameters'],
                                               requestArgs)

    # Rewrite query using pagination
    if query_metadata['type'] == 'SelectQuery' and 'pagination' in query_metadata:
        rewritten_query = gquery.paginate_query(rewritten_query, query_metadata['pagination'], requestArgs)

    resp = None
    headers = {}

    # If we have a mime field, we load the remote dump and query it locally
    if 'mime' in query_metadata and query_metadata['mime']:
        glogger.debug(
            "Detected {} MIME type, proceeding with locally loading remote dump".format(query_metadata['mime']))
        g = Graph()
        try:
            query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)
            g.parse(endpoint, format=query_metadata['mime'])
            glogger.debug("Local RDF graph loaded successfully with {} triples".format(len(g)))
        except Exception as e:
            glogger.error(e)
        results = g.query(rewritten_query, result='sparql')
        # Prepare return format as requested
        resp_string = ""
        if 'application/json' in acceptHeader or (content and 'application/json' in mime_types[content]):
            resp_string = results.serialize(format='json')
            glogger.debug("Results of SPARQL query against locally loaded dump: {}".format(resp_string))
        elif 'text/csv' in acceptHeader or (content and 'text/csv' in mime_types.mimetypes[content]):
            resp_string = results.serialize(format='csv')
            glogger.debug("Results of SPARQL query against locally loaded dump: {}".format(resp_string))
        else:
            return 'Unacceptable requested format', 415, {}
        glogger.debug("Finished processing query against RDF dump, end of use case")
        del g

    # Check for INSERT/POST
    elif query_metadata['type'] == 'InsertData':
        glogger.debug("Processing INSERT query")
        # Rewrite INSERT
        rewritten_query = rewritten_query.replace("?_g_iri", "{}".format(formData.get('g')))
        rewritten_query = rewritten_query.replace("<s> <p> <o>", formData.get('data'))
        glogger.debug("INSERT query rewritten as {}".format(rewritten_query))

        # Prepare HTTP POST request
        reqHeaders = {'Accept': acceptHeader, 'Content-Type': 'application/sparql-update'}
        response = requests.post(endpoint, data=rewritten_query, headers=reqHeaders, auth=auth)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = response.text
        headers['Content-Type'] = response.headers['Content-Type']

    # If there's no mime type, the endpoint is an actual SPARQL endpoint
    else:
        # requestedMimeType = static.mimetypes[content] if content else acceptHeader
        # result, contentType = sparql.getResponseText(endpoint, query, requestedMimeType)
        reqHeaders = {'Accept': acceptHeader}
        if content:
            reqHeaders = {'Accept': mime_types[content]}
        data = {'query': rewritten_query}

        glogger.debug('Sending HTTP request to SPARQL endpoint with params: {}'.format(data))
        glogger.debug('Sending HTTP request to SPARQL endpoint with headers: {}'.format(reqHeaders))
        glogger.debug('Sending HTTP request to SPARQL endpoint with auth: {}'.format(auth))
        response = requests.get(endpoint, params=data, headers=reqHeaders, auth=auth)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = response.text
        headers['Content-Type'] = response.headers['Content-Type']

    # If the query is paginated, set link HTTP headers
    # if pagination:
    #     # Get number of total results
    #     count = gquery.count_query_results(rewritten_query, endpoint)
    #     pageArg = requestArgs.get('page', None)
    #     headerLink = pageUtils.buildPaginationHeader(count, pagination, pageArg, requestUrl)
    #     headers['Link'] = headerLink

    # if 'proto' in query_metadata:  # sparql transformer
    #     resp = SPARQLTransformer.post_process(json.loads(resp), query_metadata['proto'], query_metadata['opt'])

    return resp, 200, headers
