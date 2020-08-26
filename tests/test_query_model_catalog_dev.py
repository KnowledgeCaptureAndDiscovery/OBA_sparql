import unittest
from typing import Dict

from obasparql import QueryManager
from obasparql.static import QUERY_TYPE_GET_ALL_USER, QUERY_TYPE_GET_ONE_USER
from tests.settings import model_catalog_queries_dev, model_catalog_context_dev, model_catalog_endpoint_dev, \
    model_catalog_graph_base_dev, model_catalog_prefix_dev


class TestQuery(unittest.TestCase):
    @staticmethod
    def generate_graph(username):
        return "{}{}".format(model_catalog_graph_base_dev, username)

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=model_catalog_queries_dev,
                                          context_dir=model_catalog_context_dev,
                                          endpoint=model_catalog_endpoint_dev,
                                          named_graph_base=model_catalog_graph_base_dev,
                                          uri_prefix=model_catalog_prefix_dev)

        username = "mint@isi.edu"
        self.username = self.generate_graph(username)

    def test_get_all_with_pagination(self):
        """
        Test to obtain all the resources related to type
        """
        owl_class_name = "ModelConfiguration"
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfiguration"
        query_type = QUERY_TYPE_GET_ALL_USER

        grlc_request_args = {
            "type": owl_class_uri,
            "g": self.username,
            "per_page": 2,
            "page": 1
        }

        results = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
                                                  query_type=query_type, request_args=grlc_request_args)

    def test_get_all_with_pagination_dataset(self):
        """
        Test to obtain all the resources related to type
        """
        owl_class_name = "ModelConfiguration"
        owl_class_uri = "https://w3id.org/okn/o/sd#DatasetSpecification"
        query_type = QUERY_TYPE_GET_ALL_USER

        grlc_request_args = {
            "type": owl_class_uri,
            "g": self.username,
        }

        results = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
                                                  query_type=query_type, request_args=grlc_request_args)


    def test_get_one(self):
        """
        Test to obtain one resource by its uri
        """
        owl_class_name = "ModelConfiguration"
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfiguration"
        resource_uri = "https://w3id.org/okn/i/mint/pihm-v2"
        query_type = QUERY_TYPE_GET_ONE_USER

        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.username
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertEqual(len(resource), 1)
        print(resource)
        # There is an inconsistency in rdf:types, some are returned with the full URI.
        # The model config type is always returned second
        self.assertIn("https://w3id.org/okn/o/sdm#ModelConfiguration",
                      (resource[0]['http://www.w3.org/1999/02/22-rdf-syntax-ns#type'])[1]['id'])
        self.assertEqual(resource[0]["id"], resource_uri)


    def test_get_one_setup_custom(self):
        """
        Test to obtain one resource by its uri and a custon query
        """
        owl_class_name = "custom"
        resource_uri = "https://w3id.org/okn/i/mint/cycles-0.9.4-alpha-simple-pongo"
        resource_type_uri = "https://w3id.org/okn/o/sdm#ModelConfigurationSetup"
        query_type = "custom_modelconfigurationsetups"

        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.username
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=resource_type_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertEqual(len(resource), 1)
        self.assertEqual(resource[0]["id"], resource_uri)


if __name__ == '__main__':
    unittest.main()