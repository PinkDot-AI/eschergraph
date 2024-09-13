from __future__ import annotations

from typing import Any
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from eschergraph.agents.jinja_helper import process_template
from eschergraph.config import GLOBAL_SEARCH_TEMPLATE
from eschergraph.config import MAIN_COLLECTION
from eschergraph.graph.search.attribute_search import AttributeSearch
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes
from eschergraph.persistence.vector_db.vector_search_result import VectorSearchResult

if TYPE_CHECKING:
  from eschergraph.graph import Graph


def global_search(
  graph: Graph, query: str, doc_filter: Optional[list[UUID]] = None
) -> str:
  """Search a graph globally through its communities.

  Note that the findings for a community should be sorted, this is the default behavior when building a graph.

  Args:
    graph (Graph): The graph object representing the data structure.
    query (str): The query string used to search within the graph.
    doc_filter: (Optional[list[UUID]]) The optional list of document id's to filter for.

  Returns:
    str: The processed response from the graph model based on the search results..
  """
  extractions: list[AttributeSearch] = get_relevant_extractions(
    graph, query, doc_filter
  )
  ans_template: str = GLOBAL_SEARCH_TEMPLATE
  context: str = "\n".join([a.text for a in extractions])
  full_prompt: str = process_template(
    ans_template, {"CONTEXT": context, "QUERY": query}
  )
  response: str | None = graph.model.get_plain_response(full_prompt)
  if not response:
    return ""

  return response


def get_relevant_extractions(
  graph: Graph, prompt: str, doc_filter: Optional[list[UUID]] = None
) -> list[AttributeSearch]:
  """Extract relevant attributes from the graph based on the search prompt.

  Args:
    graph (Graph): The graph object containing the data to search through.
    prompt (str): The query prompt used to perform the attribute search.
    doc_filter: (Optional[list[UUID]]) The optional list of document id's to filter for.

  Returns:
    list[AttributeSearch]: A list of relevant attributes extracted from the graph, after filtering and reranking.
  """
  # Perform the search at level 1
  search_metadata: dict[str, Any] = {"level": 1}

  if doc_filter:
    search_metadata["document_id"] = [str(id) for id in doc_filter]

  attributes_results: list[VectorSearchResult] = graph.vector_db.search(
    query=prompt,
    top_n=15,
    metadata=search_metadata,
    collection_name=MAIN_COLLECTION,
  )

  results: list[AttributeSearch] = rerank_and_filter_attributes(
    graph=graph, query=prompt, attributes_results=attributes_results, threshold=0
  )
  return results
