import unittest
from typing import Dict

from obasparql import QueryManager
from obasparql.static import QUERY_TYPE_GET_ALL_USER, QUERY_TYPE_GET_ONE_USER
from tests.settings import model_catalog_queries, model_catalog_context, model_catalog_endpoint, \
    model_catalog_graph_base, model_catalog_prefix


class TestQuery(unittest.TestCase):
    @staticmethod
    def generate_graph(username):
        return "{}{}".format(model_catalog_graph_base, username)

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=model_catalog_queries,
                                          context_dir=model_catalog_context,
                                          endpoint=model_catalog_endpoint,
                                          named_graph_base=model_catalog_graph_base,
                                          uri_prefix=model_catalog_prefix)

        username = "mint@isi.edu"
        self.username = self.generate_graph(username)
        self.email = username

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

        results = self.query_manager.run_query_get(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
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

        results = self.query_manager.run_query_get(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
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

        resource = self.query_manager.run_query_get(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertIn("ModelConfiguration", resource['type'])
        self.assertEqual(resource['id'], resource_uri)

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

        resource = self.query_manager.run_query_get(query_directory=owl_class_name, owl_class_uri=resource_type_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertEqual(resource["id"], resource_uri)

    def test_get_resource_custom(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfigurationSetup"
        owl_class_name = "ModelConfigurationSetup"
        custom_query_name = "custom_modelconfigurationsetups"
        username = self.email
        _id = "https://w3id.org/okn/i/mint/cycles-0.9.4-alpha-simple-pongo"
        response = self.query_manager.get_resource(id=_id,
                                                   username=username,
                                                   custom_query_name=custom_query_name,
                                                   rdf_type_uri=owl_class_uri,
                                                   rdf_type_name=owl_class_name)
        assert response

    def test_get_one_resource(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfigurationSetup"
        owl_class_name = "ModelConfigurationSetup"
        username = self.email
        _id = "https://w3id.org/okn/i/mint/cycles-0.9.4-alpha-simple-pongo"
        response = self.query_manager.get_resource(id=_id,
                                                   username=username,
                                                   rdf_type_uri=owl_class_uri,
                                                   rdf_type_name=owl_class_name)
        assert response

    def test_get_all_resources(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfigurationSetup"
        owl_class_name = "ModelConfigurationSetup"
        username = self.email
        response = self.query_manager.get_resource(username=username,
                                                   rdf_type_uri=owl_class_uri,
                                                   rdf_type_name=owl_class_name)
        assert response


    def test_get_all_resources_pagination(self):
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfigurationSetup"
        owl_class_name = "ModelConfigurationSetup"
        per_page = 2
        page = 1
        username = self.email
        response = self.query_manager.get_resource(username=username,
                                                   page=page,
                                                   per_page=per_page,
                                                   rdf_type_uri=owl_class_uri,
                                                   rdf_type_name=owl_class_name)
        #todo: check pagination
        #assert len(response) == 2
