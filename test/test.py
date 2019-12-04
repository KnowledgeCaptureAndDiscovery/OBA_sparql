import unittest
from typing import Dict

from obasparql.static import GET_ALL_USER_QUERY, GET_ONE_USER_QUERY
from test.settings import GRAPH_BASE, ENDPOINT
import unittest

from obasparql import QueryManager
from test.settings import QUERY_DIRECTORY, CONTEXT_DIRECTORY, QUERIES_TYPES


class TestSum(unittest.TestCase):
    @staticmethod
    def generate_graph(username):
        return "{}{}".format(GRAPH_BASE, username)

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=QUERY_DIRECTORY,
                                          context_dir=CONTEXT_DIRECTORY,
                                          queries_types=QUERIES_TYPES)
        username = "mint@isi.edu"
        self.username = self.generate_graph(username)

    def test_get_all(self):
        """
        Test to obtain all the resources related to type
        """
        owl_class_name = "ModelConfiguration"
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfiguration"
        query_type = GET_ALL_USER_QUERY

        #grlc args
        grlc_request_args: Dict[str, str] = {
            "type": owl_class_uri,
            "g": self.username
        }


        self.query_manager.obtain_query(query_directory=owl_class_name,
                                        owl_class_uri=owl_class_uri,
                                        query_type=query_type,
                                        endpoint=ENDPOINT,
                                        request_args=grlc_request_args)


    def test_get_one(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "ModelConfiguration"
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfiguration"
        resource_uri = "https://w3id.org/okn/i/mint/pihm-v2"
        query_type = GET_ONE_USER_QUERY

        #grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.username
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name,
                                                   owl_class_uri=owl_class_uri,
                                                   query_type=query_type,
                                                   endpoint=ENDPOINT,
                                                   request_args=request_args)
        self.assertEqual(len(resource), 1)
        self.assertEqual(resource[0]["id"], resource_uri)

    def test_get_one_setup_custom(self):
        """
        Test to obtain one resource by the uri and a custon query
        """
        owl_class_name = "custom"
        resource_uri = "https://w3id.org/okn/i/mint/cycles-0.9.4-alpha-simple-pongo"
        resource_type_uri = "https://w3id.org/okn/o/sdm#ModelConfigurationSetup"
        query_type = "get_setup"

        #grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.username
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name,
                                                   owl_class_uri=resource_type_uri,
                                                   query_type=query_type,
                                                   endpoint=ENDPOINT,
                                                   request_args=request_args)
        self.assertEqual(len(resource), 1)
        self.assertEqual(resource[0]["id"], resource_uri)

if __name__ == '__main__':
    unittest.main()
