import typing
import uuid

primitives = typing.Union[int, str, bool, float]

def generate_graph(graph_base, username):
    return "{}{}".format(graph_base, username)

def generate_new_uri():
    return str(uuid.uuid4())
