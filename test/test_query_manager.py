import logging
import unittest
from typing import Dict

from obasparql.query_manager import dispatchSPARQLQuery, QueryManager
from obasparql.static import GET_ONE_USER_QUERY, GET_ALL_USER_QUERY
from obasparql.utils import generate_graph
from test.settings import QUERY_ENDPOINT, ENDPOINT, QUERY_DIRECTORY, CONTEXT_DIRECTORY, QUERIES_TYPES, GRAPH_BASE

logger = logging.getLogger('testing')
MINT_USERNAME = generate_graph(GRAPH_BASE, "mint@isi.edu")


class TestQueryManager(unittest.TestCase):
    def setUp(self):
        self.query_manager = QueryManager(queries_dir=QUERY_DIRECTORY,
                                          context_dir=CONTEXT_DIRECTORY,
                                          queries_types=QUERIES_TYPES)

    def test_obtain_query_get_one_user(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "Model"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Model"
        resource_uri = "https://w3id.org/okn/i/mint/CYCLES"
        query_type = GET_ONE_USER_QUERY

        #grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": MINT_USERNAME
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name,
                                                   owl_class_uri=owl_class_uri,
                                                   query_type=query_type,
                                                   endpoint=ENDPOINT,
                                                   request_args=request_args)

        logger.debug(resource)
        self.assertEqual(resource_uri, resource[0]["id"])

    def test_obtain_query_get_one_user_region_case(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "Region"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        resource_uri = "https://w3id.org/okn/i/mint/Travis"
        query_type = GET_ONE_USER_QUERY

        #grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": MINT_USERNAME
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name,
                                                   owl_class_uri=owl_class_uri,
                                                   query_type=query_type,
                                                   endpoint=ENDPOINT,
                                                   request_args=request_args)

        logger.debug(resource)
        self.assertEqual(resource_uri, resource[0]["id"])

    def test_dispatchSPARQLQuery(self):
        """
        Testing to get the resource Travis
        Travis is a Region
        Returns:
        """
        owl_class_name = "Region"
        owl_resource_iri = "https://w3id.org/okn/i/mint/Travis"
        query_directory = owl_class_name
        query_type = GET_ONE_USER_QUERY

        endpoint = QUERY_ENDPOINT
        request_args: Dict[str, str] = {
            "resource": owl_resource_iri,
            "g": MINT_USERNAME
        }

        query_template = getattr(self.query_manager, query_directory)[query_type]

        resp, status, headers = dispatchSPARQLQuery(raw_sparql_query=query_template,
                            loader=None,
                            requestArgs=request_args,
                            acceptHeader="application/ld+json",
                            content=None,
                            formData=None,
                            requestUrl=None,
                            endpoint=endpoint)

    #     def test_framed_get_all(self):
    #         owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
    #         owl_resource_uri = "https://w3id.org/okn/i/mint/Travis"
    #         response = '''{
    #   "@graph" : [ {
    #     "@id" : "https://w3id.org/okn/i/mint/Texas",
    #     "@type" : "https://w3id.org/okn/o/sdm#Region",
    #     "label" : "Texas (USA)"
    #   }, {
    #     "@id" : "https://w3id.org/okn/i/mint/Travis",
    #     "@type" : "https://w3id.org/okn/o/sdm#Region",
    #     "label" : "Travis",
    #     "description" : "Travis (Texas)",
    #     "partOf" : "https://w3id.org/okn/i/mint/Texas"
    #   } ],
    #   "@context" : {
    #     "label" : {
    #       "@id" : "http://www.w3.org/2000/01/rdf-schema#label"
    #     },
    #     "partOf" : {
    #       "@id" : "https://w3id.org/okn/o/sdm#partOf",
    #       "@type" : "@id"
    #     },
    #     "description" : {
    #       "@id" : "https://w3id.org/okn/o/sd#description"
    #     },
    #     "sd" : "https://w3id.org/okn/o/sd#",
    #     "rdfs" : "http://www.w3.org/2000/01/rdf-schema#"
    #   }
    # }'''
    #
    #         framed = self.query_manager.frame_results(response, owl_class_uri, owl_resource_uri)
    #         logger.info(framed)
    #         self.assertEqual(owl_resource_uri, framed[0]["id"])

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

        framed = self.query_manager.frame_results(response, owl_class_uri, owl_resource_uri)
        self.assertEqual(owl_resource_uri, framed[0]["id"])

if __name__ == '__main__':
    unittest.main()
