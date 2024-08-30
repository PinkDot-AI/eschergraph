from __future__ import annotations

from typing import TYPE_CHECKING

from eschergraph.agents.jinja_helper import process_template
from eschergraph.graph.search.quick_search import AttributeSearch
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes

if TYPE_CHECKING:
  from eschergraph.graph import Graph


def global_search(graph: Graph, query: str) -> str | None:
  """Search a graph globally through its communities.

  Note that the findings for a community should be sorted, this is the default behavior when building a graph.

  Args:
    graph (Graph): The graph object representing the data structure.
    query (str): The query string used to search within the graph.

  Returns:
    str | None: The processed response from the graph model based on the search results, or None if no results are found.
  """
  extractions: list[AttributeSearch] = _get_relevant_extractions(graph, query)

  ans_template = "search/question_with_context.jinja"
  context = "\n".join(extractions)
  full_prompt = process_template(ans_template, {"CONTEXT": context, "QUERY": query})
  return graph.model.get_plain_response(full_prompt)


def _get_relevant_extractions(graph: Graph, prompt: str) -> list[AttributeSearch]:
  """Extract relevant attributes from the graph based on the search prompt.

  Args:
    graph (Graph): The graph object containing the data to search through.
    prompt (str): The query prompt used to perform the attribute search.

  Returns:
    list[AttributeSearch]: A list of relevant attributes extracted from the graph, after filtering and reranking.
  """
  # Perform the final search for attributes
  attributes_results = graph.vector_db.format_search_results(
    graph.vector_db.search(
      query=prompt,
      top_n=15,
      metadata={"level": 1},
      collection_name="main_collection",
    )
  )
  relevent_extractions: list[str] = [
    a["chunk"] for a in attributes_results if isinstance(a["chunk"], str)
  ]

  results: list[AttributeSearch] = rerank_and_filter_attributes(
    prompt, relevent_extractions, attributes_results, threshold=0
  )
  return results
