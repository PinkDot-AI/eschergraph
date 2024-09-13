from __future__ import annotations

from typing import TYPE_CHECKING

from eschergraph.agents.jinja_helper import process_template
from eschergraph.config import MAIN_COLLECTION
from eschergraph.graph.search.attribute_search import AttributeSearch
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes
from eschergraph.persistence.vector_db.vector_search_result import VectorSearchResult

if TYPE_CHECKING:
  from eschergraph.graph import Graph


def global_search(graph: Graph, query: str) -> str:
  """Search a graph globally through its communities.

  Note that the findings for a community should be sorted, this is the default behavior when building a graph.

  Args:
    graph (Graph): The graph object representing the data structure.
    query (str): The query string used to search within the graph.

  Returns:
    str: The processed response from the graph model based on the search results..
  """
  extractions: list[AttributeSearch] = get_relevant_extractions(graph, query)
  ans_template = "search/global_search_context.jinja"
  context = "\n".join([a.text for a in extractions])
  full_prompt = process_template(ans_template, {"CONTEXT": context, "QUERY": query})
  response: str | None = graph.model.get_plain_response(full_prompt)
  if not response:
    return ""

  return response


def get_relevant_extractions(graph: Graph, prompt: str) -> list[AttributeSearch]:
  """Extract relevant attributes from the graph based on the search prompt.

  Args:
    graph (Graph): The graph object containing the data to search through.
    prompt (str): The query prompt used to perform the attribute search.

  Returns:
    list[AttributeSearch]: A list of relevant attributes extracted from the graph, after filtering and reranking.
  """
  # Perform the search at level 1
  attributes_results: list[VectorSearchResult] = graph.vector_db.search(
    query=prompt,
    top_n=15,
    metadata={"level": 1},
    collection_name=MAIN_COLLECTION,
  )

  results: list[AttributeSearch] = rerank_and_filter_attributes(
    graph=graph, query=prompt, attributes_results=attributes_results, threshold=0
  )
  return results
