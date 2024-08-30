from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import define
from dotenv import load_dotenv

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.reranker import RerankerResult
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.persistence.metadata import Metadata

if TYPE_CHECKING:
  from eschergraph.graph import Graph

load_dotenv()
RAG_SEARCH = "search/rag_prompt.jinja"


@define
class AttributeSearch:
  """This is the dataclass for the attribute search object."""

  text: str
  metadata: Metadata | None
  parent_node: str


def quick_search(
  graph: Graph,
  query: str,
) -> str:
  """Performs a quick search and Retrieval-Augmented Generation (RAG) using the vector database and language model.

  Args:
      query (str): The input query string to search for relevant attributes in the graph.
      graph (Graph): The graph on which the quick search is performed

  Returns:
      list[AttributeSearch]: A list of AttributeSearch objects containing the response generated by the language model.
  """
  # Retrieve and rank attributes based on the query
  if query.strip() == "":
    return "please ask a question"
  attributes: list[AttributeSearch] = _get_attributes(graph, query)
  chunks_string: str = ""
  if len(attributes) == 0:
    chunks_string = "Nothing found in the graph regarding this question!"
  else:
    for a in attributes:
      chunks_string += a.text + "\n"
  prompt: str = process_template(
    RAG_SEARCH, data={"chunks": chunks_string, "query": query}
  )
  answer: str | None = graph.model.get_plain_response(prompt)
  if answer:
    return answer
  else:
    return "Something went wrong with generating the answer"


def _get_attributes(graph: Graph, query: str) -> list[AttributeSearch]:
  """Gets and ranks all relevant objects in the graph based on the query.

  Args:
      query (str): The input query string used to search and rank attributes.
      graph (Graph): The graph on which the quick search is performed

  Returns:
      list[AttributeSearch]: A list of AttributeSearch objects representing the ranked attributes relevant to the query.
  """
  # Extract nodes/entities from the query using the language model
  extracted_nodes: list[str] = extract_entities_from(query=query, llm=graph.model)

  # Initialize search metadata for attributes
  search_metadata = {"level": 0}

  # Perform initial search for nodes if any extracted entities are found
  if extracted_nodes:
    results = graph.vector_db.format_search_results(
      graph.vector_db.search(
        query=", ".join(extracted_nodes),
        top_n=10,
        collection_name="node_name_collection",
      )
    )
    filtered_nodes = [r["chunk"] for r in results]

    # Add filtering conditions to the search metadata if nodes were found
    if filtered_nodes:
      search_metadata = {
        "$and": [
          {"level": 0},
          {
            "$or": [
              {"entity1": {"$in": filtered_nodes}},
              {"entity2": {"$in": filtered_nodes}},
            ]
          },
        ]
      }

  # Perform the final search for attributes
  attributes_results = graph.vector_db.format_search_results(
    graph.vector_db.search(
      query=query,
      top_n=30,
      metadata=search_metadata,
      collection_name="main_collection",
    )
  )
  attributes_string: list[str] = [
    a["chunk"] for a in attributes_results if isinstance(a["chunk"], str)
  ]

  # Filter and reformat the reranked attributes before returning them
  return rerank_and_filter_attributes(
    query, attributes_string, attributes_results, threshold=0.18
  )


def rerank(query: str, text_list: list[str], top_n: int = 10) -> list[RerankerResult]:
  """Rerank a list of texts based on their relevance to a given query.

  This function uses the JinaReranker to reorder the input texts based on their
  relevance to the provided query. It returns the top N results.

  Args:
      query (str): The query string used as the basis for reranking.
      text_list (list[str]): A list of text strings to be reranked.
      top_n (int, optional): The number of top results to return. Defaults to 10.
                             If top_n is greater than the length of text_list,
                             all results will be returned.

  Returns:
      list[RerankerResult]: A list of RerankerResult objects representing the
      reranked texts. Each RerankerResult typically contains the reranked text
      and its relevance score. The list is sorted in descending order of relevance..
  """
  reranked_attributes: list[RerankerResult] = JinaReranker().rerank(
    query=query,
    text_list=text_list,
    top_n=top_n,
  )
  return reranked_attributes


def rerank_and_filter_attributes(
  query: str,
  attributes_string: list[str],
  attributes_results: list[dict[str, UUID | int | str | float | dict[str, Any]]],
  threshold: int = 0,
) -> list[AttributeSearch]:
  """Filters and reformats a list of reranked attributes based on relevance score.

  Args:
      query (str): the regarding question in the search
      attributes_string (list[str]): a list of attributes as strings for reranking
      attributes_results (list[dict[str, UUID | int | str | float | dict[str, Any]]]):
          A list of dictionaries containing the original search results with associated metadata.
      threshold (int): is the reranker threshhold

  Returns:
      list[AttributeSearch]: A list of AttributeSearch objects that have been filtered by relevance
      score and enriched with the corresponding metadata and parent nodes.
  """
  # Preprocess attributes_results into a dictionary for quick lookups
  reranked_attributes: list[RerankerResult] = rerank(
    query, attributes_string, top_n=len(attributes_string)
  )

  results_dict: dict[str, dict[str, Any]] = {
    a["chunk"]: a["metadata"]
    for a in attributes_results
    if isinstance(a["chunk"], str) and isinstance(a["metadata"], dict)
  }

  attributes_filtered: list[AttributeSearch] = []

  for r in reranked_attributes:
    if r.relevance_score <= threshold:
      break

    # Direct lookup from the dictionary
    metadata = results_dict.get(r.text)

    if metadata:
      # Create the AttributeSearch object with the metadata and parent nodes
      obj = AttributeSearch(
        text=r.text,
        metadata=None,
        parent_node="",
      )

      attributes_filtered.append(obj)

  return attributes_filtered


def extract_entities_from(query: str, llm: ModelProvider) -> list[str]:
  """Extract entities from query.

  Args:
      query (str): Text
      llm (ModelProvider): A large language ModelProvider class
  Returns:
      List[str]: list of entities
  """
  entity_extraction_template = "search/entity_extraction.jinja"
  prompt = process_template(
    entity_extraction_template,
    {"query": query},
  )
  res = llm.get_json_response(prompt=prompt)
  if not res:
    raise ExternalProviderException("Empty message response while extracting entities")
  try:
    return res["entities"]
  except:
    raise ExternalProviderException("jsonify failed at extracting entities from query")
