import logging
import unittest
from pathlib import Path

from obasparql import QueryManager
from test.settings import QUERY_DIRECTORY, CONTEXT_DIRECTORY, QUERIES_TYPES


class BaseTestCase(unittest.TestCase):
    def __init__(self):
        logging_file = Path(__file__).parent.parent / "logging_config.ini"
        logging.config.fileConfig(logging_file)

        self.query_manager = QueryManager(queries_dir=QUERY_DIRECTORY,
                                          context_dir=CONTEXT_DIRECTORY,
                                          queries_types=QUERIES_TYPES)
