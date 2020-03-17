import json
import logging.config
import unittest
from pathlib import Path
from typing import Dict
from pyld import jsonld

from obasparql.static import GET_ALL_USER_QUERY, GET_ONE_USER_QUERY
from obasparql.utils import generate_graph
from test.settings import GRAPH_BASE, ENDPOINT
import unittest

from obasparql import QueryManager
from test.settings import QUERY_DIRECTORY, CONTEXT_DIRECTORY, QUERIES_TYPES
from obasparql.query_manager import dispatchSPARQLQuery

MINT_USERNAME = generate_graph(GRAPH_BASE, "mint@isi.edu")


class TestFrame(unittest.TestCase):
    logger = logging.getLogger('testing')

    @staticmethod
    def write_json_to_file(data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=QUERY_DIRECTORY,
                                          context_dir=CONTEXT_DIRECTORY,
                                          queries_types=QUERIES_TYPES)

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
            "g": MINT_USERNAME
        }
        response = self.query_manager.obtain_query(query_directory=owl_class_name,
                                              owl_class_uri=owl_class_uri,
                                              query_type=query_type,
                                              endpoint=ENDPOINT,
                                              request_args=request_args)
        self.assertTrue(response)
        for author in response[0]["author"]:
            self.assertIsInstance(author, dict)
        for author in response[0]["hasContactPerson"]:
            self.assertIsInstance(author, dict)


if __name__ == '__main__':
    unittest.main()
