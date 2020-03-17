import logging
import unittest
from pathlib import Path

from obasparql import QueryManager
from test.settings import QUERY_DIRECTORY, CONTEXT_DIRECTORY, QUERIES_TYPES

logging_file = Path(__file__).parent.parent / "logging_config.ini"
try:
    logging.config.fileConfig(logging_file)
except:
    logging.error("Logging config file does not exist {}".format(logging_file))
    exit(0)
logger = logging.getLogger(__name__)

class BaseTestCase(unittest.TestCase):
    def __init__(self):
        logger.error("Starting")
        self.query_manager = QueryManager(queries_dir=QUERY_DIRECTORY,
                                          context_dir=CONTEXT_DIRECTORY,
                                          queries_types=QUERIES_TYPES)
