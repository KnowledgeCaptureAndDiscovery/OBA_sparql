import unittest
import json
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

        self.username = "mint@isi.edu"
        self.usergraph = self.generate_graph(self.username)

    def test_get_all_with_pagination(self):
        """
        Test to obtain all the resources related to type
        """
        owl_class_name = "ModelConfiguration"
        owl_class_uri = "https://w3id.org/okn/o/sdm#ModelConfiguration"
        query_type = QUERY_TYPE_GET_ALL_USER

        grlc_request_args = {
            "type": owl_class_uri,
            "g": self.usergraph,
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
            "g": self.usergraph,
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
            "g": self.usergraph
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertEqual(len(resource), 1)
        self.assertIn("ModelConfiguration", resource[0]['type'][1])
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
            "g": self.usergraph
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=resource_type_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertEqual(len(resource), 1)
        self.assertEqual(resource[0]["id"], resource_uri)

    def test_post_simple(self):
        """
        Test posting a simple resource. Post a person with name and email.
        """
        owl_class_uri = "https://w3id.org/okn/o/sd#Person"
        json_body = """ {
            "email": [
              "test@test.test"
            ],
            "label": [
              "Test Person"
            ],
            "type": [ 
                "https://w3id.org/okn/o/sd#Person"
                ]
        }"""
        body = json.loads(json_body)
        body, response, nothing = self.query_manager.post_resource(self.username,body,owl_class_uri)
        self.assertEqual(response,201)
        # Test if we can find the resource
        resource_id = body["id"]
        print(resource_id)
        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_id,
            "g": self.usergraph
        }
        query_type = QUERY_TYPE_GET_ONE_USER
        inserted_resource = self.query_manager.obtain_query(query_directory="Person",
                                                                     owl_class_uri=owl_class_uri,
                                                   query_type=query_type, request_args=request_args)
        # if result is found, test passed.
        self.assertEqual(len(inserted_resource), 1)

    def test_post_simple_no_type(self):
        """
        Test posting a simple person resource. The person is not inserted with class Person type.
        """
        owl_class_uri = "https://w3id.org/okn/o/sd#Person"
        json_body = """ {
                    "email": [
                      "test@test.test"
                    ],
                    "label": [
                      "Test Person"
                    ]
                }"""
        body = json.loads(json_body)
        body, response, nothing = self.query_manager.post_resource(self.username, body, owl_class_uri)
        self.assertEqual(response, 201)
        # Test if we can find the resource
        resource_id = body["id"]
        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_id,
            "g": self.usergraph
        }
        query_type = QUERY_TYPE_GET_ONE_USER
        inserted_resource = self.query_manager.obtain_query(query_directory="Person",
                                                            owl_class_uri=owl_class_uri,
                                                            query_type=query_type, request_args=request_args)
        # if result is found, test passed.
        self.assertEqual(len(inserted_resource), 1)

    def test_post_simple_existing_id(self):
        """
        Test inserting an id as part of the resource. The resource should not be created (error).
        """
        owl_class_name = "Person"
        owl_class_uri = "https://w3id.org/okn/o/sd#Person"
        json_body = """ {
                    "email": [
                      "test@test.test"
                    ],
                    "label": [
                      "Test Person"
                    ],
                    "id":"https://w3id.org/okn/i/mint/test_person"
                }"""
        body = json.loads(json_body)
        body, response, nada = self.query_manager.post_resource(self.username, body, owl_class_uri)
        self.assertEqual(407,response)

    def test_post_complex(self):
        """
        Test posting a resource which contains another resource (e.g. region with another region)
        The higher level region has already an id
        """
        owl_class_name = "Region"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        json_body = """{
        "label": [
          "Ethiopia"
        ],
        "partOf": [
          {
            "id": "https://w3id.org/okn/i/mint/Africa",
            "label": [
            "Africa"
            ],
            "type": [
              "Region"
            ]
          }
        ],
        "type": [
          "Region"
        ]
        }"""
        body = json.loads(json_body)
        body, response, nothing = self.query_manager.post_resource(self.username, body, owl_class_uri)
        self.assertEqual(response, 201)
        # Test if we can find the resource
        resource_id = body["id"]
        print(resource_id)
        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_id,
            "g": self.usergraph
        }
        query_type = QUERY_TYPE_GET_ONE_USER
        inserted_resource = self.query_manager.obtain_query(query_directory="Person",
                                                            owl_class_uri=owl_class_uri,
                                                            query_type=query_type, request_args=request_args)
        # if result is found, test passed.
        self.assertEqual(len(inserted_resource), 1)

    def test_post_complex_list(self):
        """
        Test posting a resource which contains a list of 2 resources:
        Madrid is part of Comunidad de Madrid.
        Madrid is also part of Spain.
        """
        owl_class_name = "Region"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        json_body = """{
        "label": [
          "Madrid"
        ],
        "partOf": [
          {
            "label": [
             "Comunidad de Madrid"
            ],
            "type": [
              "Region"
            ]
          },
          {
            "label": [
            "Spain"
            ],
            "type": [
              "Region"
            ]
          }
        ],
        "type": [
          "Region"
        ]
        }"""
        body = json.loads(json_body)
        body, response, nothing = self.query_manager.post_resource(self.username, body, owl_class_uri)
        self.assertEqual(response, 201)
        # Test if we can find the resource
        resource_id = body["id"]
        print(resource_id)
        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_id,
            "g": self.usergraph
        }
        query_type = QUERY_TYPE_GET_ONE_USER
        inserted_resource = self.query_manager.obtain_query(query_directory="Region",
                                                            owl_class_uri=owl_class_uri,
                                                            query_type=query_type, request_args=request_args)
        # if result is found and has 2 partOf resources, test passed.
        self.assertEqual(len(inserted_resource[0]["partOf"]), 2)

    def test_post_complex_subresources(self):
        """
        Test posting a resource which contains a chain of 4 resources:
        Madrid is part of Spain, which is part of Europe, which is part of Earth
        """
        owl_class_name = "Region"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Region"
        json_body = """{
        "label": [
          "Madrid"
        ],
        "partOf": [
          {
            "label": [
            "Spain"
            ],
            "type": [
              "Region"
            ],
            "partOf": [
              {
                "label": [
                "Europe"
                ],
                "type": [
                  "Region"
                ],
                "partOf": [
                  {
                    "label": [
                    "Earth"
                    ],
                    "type": [
                      "Region"
                    ]
                  }
                ]
              }
            ]
          }
        ],
        "type": [
          "Region"
        ]
        }"""
        body = json.loads(json_body)
        body, response, nothing = self.query_manager.post_resource(self.username, body, owl_class_uri)
        self.assertEqual(response, 201)
        # Test if we can find the resource
        resource_id = body["id"]
        print(resource_id)
        # grlc args
        request_args: Dict[str, str] = {
            "resource": resource_id,
            "g": self.usergraph
        }
        query_type = QUERY_TYPE_GET_ONE_USER
        inserted_resource = self.query_manager.obtain_query(query_directory="Region",
                                                            owl_class_uri=owl_class_uri,
                                                            query_type=query_type, request_args=request_args)
        # if result is found and is part of part of part of Earth, then test pass
        self.assertEqual(len(inserted_resource), 1)
        self.assertIn("Earth",(((body["partOf"])[0]["partOf"])[0]["partOf"])[0]["label"])

    def test_delete(self):
        """
        Test deleting a simple resource. The resource gets inserted first.
        """
        owl_class_uri = "https://w3id.org/okn/o/sd#Person"
        json_body = """ {
                    "email": [
                      "test@test.test"
                    ],
                    "label": [
                      "Test Person"
                    ],
                    "type": [ 
                        "https://w3id.org/okn/o/sd#Person"
                        ]
                }"""
        body = json.loads(json_body)
        body, response, nothing = self.query_manager.post_resource(self.username, body, owl_class_uri)
        self.assertEqual(response, 201)
        # Delete inserted resource
        resource_id = body["id"]
        print(resource_id)
        body,response,nothing = self.query_manager.delete_resource(self.username,resource_id)
        self.assertEqual(202,response)

    def test_delete_malformed_query(self):
        """
        Test issuing a bad formed delete query
        """
        body, response, nothing = self.query_manager.delete_resource(".,<>non_existing_graph", "https://w3id.org/okn/i/mint/cf0592dd-31ce-431a-96e7-f8566bcabe40")
        #TODO: must return 404
        self.assertEqual(response,202)

    # def test_delete_complex_resource(self):
    #     """
    #     Test deleting a resource which contains other resources. The behavior should be as in a simple resource.
    #     TO DO
    #     """
    #     # delete resource
    #     # check resource exists
    #
    # def test_put(self):
    #     """
    #     Test posting a simple resource
    #     TO DO
    #     """
    #     # check if resource exists
    #     # create resource
    #     # check if result exists




if __name__ == '__main__':
    unittest.main()
