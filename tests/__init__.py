import logging.config
import unittest
from pathlib import Path

logging_file = Path(__file__).parent / "logging_config.ini"
try:
    logging.config.fileConfig(logging_file)
except:
    logging.error("Logging config file does not exist {}".format(logging_file), exc_info=True)
    exit(0)
logger = logging.getLogger(__name__)


class BaseTestCase(unittest.TestCase):
    def __init__(self):
        pass
