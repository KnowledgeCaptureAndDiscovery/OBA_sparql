import json
import logging
import unittest
from typing import Dict

from SPARQLWrapper import JSONLD

from obasparql.query_manager import dispatch_sparql_query, QueryManager
from obasparql.static import GET_ONE_USER_QUERY, GET_ALL_USER_QUERY, GET_ONE_QUERY
from obasparql.utils import generate_graph
from test.settings import *

logger = logging.getLogger('testing')
MINT_USERNAME = generate_graph(GRAPH_BASE, "mint@isi.edu")


class TestQueryManager(unittest.TestCase):
    def setUp(self):
        self.query_manager_model_catalog = QueryManager(queries_dir=QUERY_DIRECTORY,
                                                        context_dir=CONTEXT_DIRECTORY,
                                                        queries_types=QUERIES_TYPES)

        self.query_manager_dbpedia = QueryManager(queries_dir=QUERY_DIRECTORY_DBPEDIA,
                                                  context_dir=CONTEXT_DIRECTORY_DBPEDIA,
                                                  queries_types=QUERIES_TYPES)

    def test_obtain_query_get_one(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "Band"
        owl_class_uri = "http://dbpedia.org/ontology/Band"
        resource_uri = "http://dbpedia.org/resource/Indemnity_Act_1717"
        query_type = GET_ONE_QUERY

        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
        }

        resource = self.query_manager_dbpedia.obtain_query(query_directory=owl_class_name,
                                                           owl_class_uri=owl_class_uri,
                                                           query_type=query_type,
                                                           endpoint=ENDPOINT_DBPEDIA,
                                                           request_args=request_args)

        self.assertTrue(resource)

    def test_obtain_query_get_one_user(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "Model"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Model"
        resource_uri = "https://w3id.org/okn/i/mint/CYCLES"
        query_type = GET_ONE_USER_QUERY

        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": MINT_USERNAME
        }

        resource = self.query_manager_model_catalog.obtain_query(query_directory=owl_class_name,
                                                                 owl_class_uri=owl_class_uri,
                                                                 query_type=query_type,
                                                                 endpoint=ENDPOINT,
                                                                 request_args=request_args)

        self.assertTrue(resource)

    def test_obtain_query_get_one_user_region_case(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "Region"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        resource_uri = "https://w3id.org/okn/i/mint/Travis"
        query_type = GET_ONE_USER_QUERY

        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": MINT_USERNAME
        }

        resource = self.query_manager_model_catalog.obtain_query(query_directory=owl_class_name,
                                                                 owl_class_uri=owl_class_uri,
                                                                 query_type=query_type,
                                                                 endpoint=ENDPOINT,
                                                                 request_args=request_args)

        self.assertEqual(resource_uri, resource[0]["id"])

    def test_dispatch_sparqlquery(self):
        endpoint = "http://dbpedia.org/sparql"
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
        results = dispatch_sparql_query(raw_sparql_query=query_template, request_args={}, endpoint=endpoint,
                                        return_format=JSONLD)
        self.assertIsNotNone(json.loads(results))

    def test_dispatch_sparqlquery_model_catalog(self):
        """
        Testing to get the resource Travis
        Travis is a Region
        Returns:
        """
        owl_class_name = "Region"
        owl_resource_iri = "https://w3id.org/okn/i/mint/United_States"
        query_directory = owl_class_name
        query_type = GET_ONE_USER_QUERY

        endpoint = QUERY_ENDPOINT
        request_args: Dict[str, str] = {
            "resource": owl_resource_iri,
            "g": MINT_USERNAME
        }

        query_template = getattr(self.query_manager_model_catalog, query_directory)[query_type]

        results = dispatch_sparql_query(raw_sparql_query=query_template,
                                     request_args=request_args,
                                     endpoint=endpoint,
                                     return_format=JSONLD)
        self.assertIsNotNone(json.loads(results))

    def test_framed_get_one(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        owl_resource_uri = "https://w3id.org/okn/i/mint/Travis"
        response = '''{
  "@graph" : [ {
    "@id" : "https://w3id.org/okn/i/mint/Texas",
    "@type" : "https://w3id.org/okn/o/sdm#Region",
    "label" : "Texas (USA)"
  }, {
    "@id" : "https://w3id.org/okn/i/mint/Travis",
    "@type" : "https://w3id.org/okn/o/sdm#Region",
    "label" : "Travis",
    "description" : "Travis (Texas)",
    "partOf" : "https://w3id.org/okn/i/mint/Texas"
  } ],
  "@context" : {
    "label" : {
      "@id" : "http://www.w3.org/2000/01/rdf-schema#label"
    },
    "partOf" : {
      "@id" : "https://w3id.org/okn/o/sdm#partOf",
      "@type" : "@id"
    },
    "description" : {
      "@id" : "https://w3id.org/okn/o/sd#description"
    },
    "sd" : "https://w3id.org/okn/o/sd#",
    "rdfs" : "http://www.w3.org/2000/01/rdf-schema#"
  }
}'''

        framed = self.query_manager_model_catalog.frame_results(response, owl_class_uri, owl_resource_uri)
        self.assertEqual(owl_resource_uri, framed[0]["id"])

    def test_framed_get_one_reflexive(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        owl_resource_uri = "https://w3id.org/okn/i/mint/United_States"
        response = '''{
  "@id" : "https://w3id.org/okn/i/mint/United_States",
  "@type" : "https://w3id.org/okn/o/sdm#Region",
  "label" : "United States of America",
  "description" : "The United States of America (U.S.A. or USA), commonly known as the United States (U.S. or US) or America, is a country comprising 50 states, a federal district, five major self-governing territories, and various possessions. At 3.8 million square miles (9.8 million km2), the United States is the world's third or fourth largest country by total area and is slightly smaller than the entire continent of Europe. With a population of over 327 million people, the U.S. is the third most populous country. The capital is Washington, D.C., and the most populous city is New York City. Most of the country is located contiguously in North America between Canada and Mexico.",
  "partOf" : "https://w3id.org/okn/i/mint/America",
  "@context" : {
    "partOf" : {
      "@id" : "https://w3id.org/okn/o/sdm#partOf",
      "@type" : "@id"
    },
    "description" : {
      "@id" : "https://w3id.org/okn/o/sd#description"
    },
    "label" : {
      "@id" : "http://www.w3.org/2000/01/rdf-schema#label"
    },
    "sd" : "https://w3id.org/okn/o/sd#",
    "rdfs" : "http://www.w3.org/2000/01/rdf-schema#"
  }
}'''

        framed = self.query_manager_model_catalog.frame_results(response, owl_class_uri, owl_resource_uri)
        self.assertEqual(owl_resource_uri, framed[0]["id"])


if __name__ == '__main__':
    unittest.main()
