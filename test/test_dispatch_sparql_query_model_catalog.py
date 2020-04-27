import json
import logging
import unittest
from typing import Dict

from SPARQLWrapper import JSONLD

from obasparql.query_manager import QueryManager
from obasparql.utils import generate_graph
from test.settings import *

logger = logging.getLogger('testing')
graph_user = generate_graph(model_catalog_graph_base, "mint@isi.edu")


class TestQueryManager(unittest.TestCase):
    def setUp(self):
        self.query_manager = QueryManager(queries_dir=model_catalog_queries,
                                          context_dir=model_catalog_context,
                                          queries_types=QUERIES_TYPES,
                                          endpoint=model_catalog_endpoint,
                                          graph_base=model_catalog_graph_base,
                                          prefix=model_catalog_prefix)

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
        results = self.query_manager.dispatch_sparql_query(raw_sparql_query=query_template,
                                                           request_args={},
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

        request_args: Dict[str, str] = {
            "resource": owl_resource_iri,
            "g": graph_user
        }

        query_template = getattr(self.query_manager, query_directory)[query_type]

        results = self.query_manager.dispatch_sparql_query(raw_sparql_query=query_template,
                                                           request_args=request_args,
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

        framed = self.query_manager.frame_results(response, owl_class_uri, owl_resource_uri)
        self.assertEqual(owl_resource_uri, framed[0]["id"])

    def test_framed_get_one_reflexive(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        owl_resource_uri = "https://w3id.org/okn/i/mint/United_States"
        response = '''{
  "@graph" : [ {
    "@id" : "https://w3id.org/okn/i/mint/Texas",
    "@type" : "https://w3id.org/okn/o/sdm#Region",
    "label" : "Texas (USA)",
    "description" : "Texas is the second largest state in the United States by area (after Alaska) and population (after California). Located in the South Central region, Texas shares borders with the states of Louisiana to the east, Arkansas to the northeast, Oklahoma to the north, New Mexico to the west, and the Mexican states of Chihuahua, Coahuila, Nuevo Leon, and Tamaulipas to the southwest, and has a coastline with the Gulf of Mexico to the southeast.",
    "geo" : "https://w3id.org/okn/i/mint/Texas_Shape",
    "partOf" : "https://w3id.org/okn/i/mint/United_States"
  }, {
    "@id" : "https://w3id.org/okn/i/mint/Texas_Shape",
    "@type" : "https://w3id.org/okn/o/sdm#GeoShape",
    "label" : "Bounding box for Texas region"
  }, {
    "@id" : "https://w3id.org/okn/i/mint/United_States",
    "@type" : "https://w3id.org/okn/o/sdm#Region",
    "label" : "United States of America"
  }, {
    "@id" : "https://w3id.org/okn/o/sdm#Region",
    "@type" : "http://www.w3.org/2002/07/owl#Class"
  } ],
  "@context" : {
    "partOf" : {
      "@id" : "https://w3id.org/okn/o/sdm#partOf",
      "@type" : "@id"
    },
    "geo" : {
      "@id" : "https://w3id.org/okn/o/sdm#geo",
      "@type" : "@id"
    },
    "description" : {
      "@id" : "https://w3id.org/okn/o/sd#description"
    },
    "label" : {
      "@id" : "http://www.w3.org/2000/01/rdf-schema#label"
    },
    "rdfs" : "http://www.w3.org/2000/01/rdf-schema#"
  }
}
'''

        framed = self.query_manager.frame_results(response, owl_class_uri, owl_resource_uri)
        self.assertEqual(owl_resource_uri, framed[0]["id"])


if __name__ == '__main__':
    unittest.main()
