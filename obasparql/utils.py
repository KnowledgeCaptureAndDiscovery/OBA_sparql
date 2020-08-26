import re
import typing
import uuid

primitives = typing.Union[int, str, bool, float]


def generate_uri(graph_base, username):
    """

    Args:
        graph_base ():
        username ():

    Returns:

    """
    return "{}{}".format(graph_base, username)


def generate_new_id():
    return str(uuid.uuid4())


def convert_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
