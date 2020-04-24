import json
import logging.config
from typing import Dict

from obasparql.static import GET_ONE_USER_QUERY
from obasparql.utils import generate_graph
import unittest

from obasparql import QueryManager
from test.settings import QUERIES_TYPES
from test.settings import *

graph_user = generate_graph(model_catalog_graph_base, "mint@isi.edu")


class TestFrame(unittest.TestCase):
    logger = logging.getLogger('testing')

    @staticmethod
    def write_json_to_file(data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=model_catalog_queries,
                                          context_dir=model_catalog_context,
                                          queries_types=QUERIES_TYPES,
                                          endpoint=model_catalog_endpoint,
                                          graph_base=model_catalog_graph_base,
                                          prefix=model_catalog_prefix)

    def test_frame_author(self):
        """
        This tests query a resource with type *MODEL*
        The properties: author and hasContactPerson have the same range: Person or Organization
        IRI: https://w3id.org/okn/o/sd#author
        IRI: https://w3id.org/okn/o/sd#hasContactPerson
        Returns:

        """
        owl_class_name = "Model"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Model"
        resource_uri = "https://w3id.org/okn/i/mint/CYCLES"
        query_type = GET_ONE_USER_QUERY

        #grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": graph_user
        }
        response = self.query_manager.obtain_query(query_directory=owl_class_name, owl_class_uri=owl_class_uri,
                                                   query_type=query_type, request_args=request_args)
        self.assertTrue(response)
        for author in response[0]["author"]:
            self.assertIsInstance(author, dict)
        for author in response[0]["hasContactPerson"]:
            self.assertIsInstance(author, dict)


if __name__ == '__main__':
    unittest.main()
