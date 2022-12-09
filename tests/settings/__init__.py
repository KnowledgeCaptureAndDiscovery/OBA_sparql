from pathlib import Path

path = Path(__file__).parent.parent.parent

model_catalog_endpoint = "https://endpoint.mint.isi.edu/modelcatalog"
model_catalog_graph_base = "http://endpoint.mint.isi.edu/modelCatalog-1.8.0/data/"
model_catalog_prefix = "https://w3id.org/okn/i/mint/"
model_catalog_queries = path / "tests/model_catalog/queries/"
model_catalog_context = path / "tests/model_catalog/contexts/"

# dev endpoint version
model_catalog_endpoint_dev = model_catalog_endpoint
model_catalog_graph_base_dev = model_catalog_graph_base
model_catalog_prefix_dev = "https://w3id.org/okn/i/mint/"
model_catalog_queries_dev = path / "tests/model_catalog_dev/queries/"
model_catalog_context_dev = path / "tests/model_catalog_dev/contexts/"

# dbpedia
dbpedia_endpoint = "https://dbpedia.org/sparql"
dbpedia_prefix = "http://dbpedia.org/resource"
dbpedia_queries = path / "tests/dbpedia/queries/"
dbpedia_context = path / "tests/dbpedia/contexts/"
