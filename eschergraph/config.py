from __future__ import annotations

DEFAULT_SAVE_LOCATION: str = "./eschergraph_storage"
DEFAULT_GRAPH_NAME: str = "escher_default"
COMMUNITY_TEMPLATE: str = "community_prompt.jinja"
TEMPLATE_IMPORTANCE: str = "search/importance_rank.jinja"
JSON_BUILD: str = "json_build.jinja"
JSON_PROPERTY: str = "json_property.jinja"
MAIN_COLLECTION: str = "main_collection"
GLOBAL_SEARCH_TEMPLATE: str = "search/global_search_context.jinja"

# Configuration used for the benchmarking
QA_TUNE: str = "./eschergraph_storage/qa_tune.json"
QA_TEST: str = "./eschergraph_storage/qa_test.json"
QA_GENERATED: str = "./eschergraph_storage/qa.json"
CHUNK_FILE: str = "./eschergraph_storage/chunks.json"
