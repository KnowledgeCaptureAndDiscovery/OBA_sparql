from pathlib import Path

path = Path(__file__).parent.parent.parent

model_catalog_endpoint = "https://endpoint.mint.isi.edu/modelCatalog-1.3.0"
model_catalog_graph_base = "http://ontosoft.isi.edu:3030/modelCatalog-1.3.0/data/"
model_catalog_prefix = "https://w3id.org/okn/i/mint/"
model_catalog_queries = path / "tests/model_catalog/queries/"
model_catalog_context = path / "tests/model_catalog/contexts/"

dbpedia_endpoint = "https://dbpedia.org/sparql"
dbpedia_prefix = "http://dbpedia.org/resource"
dbpedia_queries = path / "tests/dbpedia/queries/"
dbpedia_context = path / "tests/dbpedia/contexts/"


