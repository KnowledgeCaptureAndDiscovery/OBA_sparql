from pathlib import Path

from obasparql.static import GET_ALL_QUERY, GET_ALL_RELATED_QUERY, GET_ALL_RELATED_USER_QUERY, GET_ALL_USER_QUERY, \
    GET_ONE_QUERY, GET_ONE_USER_QUERY

path = Path(__file__).parent.parent.parent

model_catalog_endpoint = "https://endpoint.mint.isi.edu/modelCatalog-1.3.0"
model_catalog_graph_base = "http://ontosoft.isi.edu:3030/modelCatalog-1.3.0/data/"
model_catalog_prefix = "https://w3id.org/okn/i/mint/"
model_catalog_queries = path / "test/model_catalog/queries/"
model_catalog_context = path / "test/model_catalog/contexts/"

# dev endpoint version
model_catalog_endpoint_dev = "https://dev.endpoint.mint.isi.edu/modelCatalog-1.5.0"
model_catalog_graph_base_dev = "http://dev.endpoint.mint.isi.edu/modelCatalog-1.5.0/data/"
model_catalog_prefix_dev = "https://w3id.org/okn/i/mint/"
model_catalog_queries_dev = path / "test/model_catalog_dev/queries/"
model_catalog_context_dev = path / "test/model_catalog_dev/contexts/"

dbpedia_endpoint = "https://dbpedia.org/sparql"
dbpedia_prefix = "http://dbpedia.org/resource"
dbpedia_queries = path / "test/dbpedia/queries/"
dbpedia_context = path / "test/dbpedia/contexts/"

QUERIES_TYPES = [GET_ALL_QUERY, GET_ALL_RELATED_QUERY, GET_ALL_RELATED_USER_QUERY, GET_ALL_USER_QUERY, GET_ONE_QUERY,
                 GET_ONE_USER_QUERY]
