from typing import Dict

import unittest

from obasparql import QueryManager
from obasparql.static import QUERY_TYPE_GET_ONE_USER, QUERIES_TYPES, QUERY_TYPE_GET_ONE
from test.settings import dbpedia_queries, dbpedia_context, dbpedia_endpoint, dbpedia_prefix


class TestQuery(unittest.TestCase):

    def setUp(self):
        self.query_manager = QueryManager(queries_dir=dbpedia_queries,
                                          context_dir=dbpedia_context,
                                          queries_types=QUERIES_TYPES,
                                          endpoint=dbpedia_endpoint,
                                          named_graph_base=None,
                                          uri_prefix=dbpedia_prefix)

    def test_obtain_query_get_one(self):
        """
        Test to obtain one resource by the uri
        """
        owl_class_name = "Band"
        owl_class_uri = "http://dbpedia.org/ontology/Band"
        resource_uri = "http://dbpedia.org/resource/Pink_Floyd"
        query_type = QUERY_TYPE_GET_ONE

        request_args: Dict[str, str] = {
            "resource": resource_uri,
        }

        resource = self.query_manager.obtain_query(query_directory=owl_class_name,
                                                   owl_class_uri=owl_class_uri,
                                                   query_type=query_type,
                                                   request_args=request_args)
        self.assertTrue(resource)


if __name__ == '__main__':
    unittest.main()
