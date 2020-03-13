import json
import logging
import unittest
from pathlib import Path
from typing import Dict
from pyld import jsonld

from obasparql.static import GET_ALL_USER_QUERY, GET_ONE_USER_QUERY
from test.settings import GRAPH_BASE, ENDPOINT
import unittest

from obasparql import QueryManager
from test.settings import QUERY_DIRECTORY, CONTEXT_DIRECTORY, QUERIES_TYPES
from obasparql.query_manager import dispatchSPARQLQuery

class TestFrame(unittest.TestCase):
    logger = logging.getLogger('testing')

    @staticmethod
    def generate_graph(username):
        return "{}{}".format(GRAPH_BASE, username)

    @staticmethod
    def write_json_to_file(data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=QUERY_DIRECTORY,
                                          context_dir=CONTEXT_DIRECTORY,
                                          queries_types=QUERIES_TYPES)
        username = "mint@isi.edu"
        self.username = self.generate_graph(username)

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
            "g": self.username
        }
        response = self.query_manager.obtain_query(query_directory=owl_class_name,
                                              owl_class_uri=owl_class_uri,
                                              query_type=query_type,
                                              endpoint=ENDPOINT,
                                              request_args=request_args)
        self.assertTrue(response)
        self.logger.debug(response)
        for author in response[0]["author"]:
            self.assertIsInstance(author, dict)
        for author in response[0]["hasContactPerson"]:
            self.assertIsInstance(author, dict)

if __name__ == '__main__':
    unittest.main()
