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
        p = Path(__file__).parent / "inputs"
        owl_class_name = "Model"
        owl_class_uri = "https://w3id.org/okn/o/sdm#Model"
        resource_uri = "https://w3id.org/okn/i/mint/CYCLES"
        query_type = GET_ONE_USER_QUERY

        #grlc args
        request_args: Dict[str, str] = {
            "resource": resource_uri,
            "g": self.username
        }

        query_template = getattr(self.query_manager, owl_class_name)[query_type]
        resp, status, headers = dispatchSPARQLQuery(raw_sparql_query=query_template,
                                                    loader=None,
                                                    requestArgs=request_args,
                                                    acceptHeader="application/ld+json",
                                                    content=None,
                                                    formData=None,
                                                    requestUrl=None,
                                                    endpoint=ENDPOINT,
                                                    auth=None)

        frame = {"@context": self.query_manager.context.copy(), "@type": owl_class_uri}

        resp_json = json.loads(resp)

        logging.error(p / "input.json")
        logging.error("====== PRINTING FRAME ======= ")
        framed = jsonld.frame(resp_json, frame, {'embed':"@always"})
        logging.error("====== PRINTING FRAMED ======= ")

        self.write_json_to_file(resp_json, p / "input.json")
        self.write_json_to_file(frame, p / "frame.json")
        self.write_json_to_file(framed, p / "framed.json")

if __name__ == '__main__':
    unittest.main()
