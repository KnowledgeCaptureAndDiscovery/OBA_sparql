import json
import logging
import unittest
from typing import Dict

from SPARQLWrapper import JSONLD

from obasparql.query_manager import QueryManager, QUERIES_TYPES
from obasparql.utils import generate_uri
from tests.settings import *

logger = logging.getLogger('testing')
graph_user = generate_uri(model_catalog_graph_base, "mint@isi.edu")


class TestQueryManager(unittest.TestCase):
    def setUp(self):
        self.query_manager = QueryManager(queries_dir=dbpedia_queries,
                                          context_dir=dbpedia_context,
                                          queries_types=QUERIES_TYPES,
                                          endpoint=dbpedia_endpoint,
                                          named_graph_base=None,
                                          uri_prefix=dbpedia_prefix)

    def test_dispatch_sparqlquery(self):
        query_template = '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    CONSTRUCT {
        <http://dbpedia.org/resource/Indemnity_Act_1717> ?predicate ?prop .
        ?prop a ?type .
        ?prop rdfs:label ?label
    }
    WHERE {
        <http://dbpedia.org/resource/Indemnity_Act_1717> ?predicate ?prop
        OPTIONAL {
            ?prop  a ?type
            OPTIONAL {
                ?prop rdfs:label ?label
            }
        }
    }
            '''
        results = self.query_manager.dispatch_sparql_query(raw_sparql_query=query_template,
                                                           request_args={},
                                                           return_format=JSONLD)
        self.assertIsNotNone(json.loads(results))


if __name__ == '__main__':
    unittest.main()
