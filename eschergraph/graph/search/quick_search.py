from __future__ import annotations

from typing import Any
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import define

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.reranker import RerankerResult
from eschergraph.config import MAIN_COLLECTION
from eschergraph.graph.node import Node
from eschergraph.graph.search.attribute_search import AttributeSearch
from eschergraph.persistence.metadata import MetadataVisual
from eschergraph.persistence.vector_db.vector_search_result import VectorSearchResult

if TYPE_CHECKING:
  from eschergraph.graph import Graph

RAG_SEARCH = "search/question_with_context.jinja"


@define
class RAGAnswer:
  """The data class for RAG answers containing the answers, sources and possible visuals."""

  answer: str
  sources: list[AttributeSearch] | None
  visuals: list[MetadataVisual] | None


def quick_search(
  graph: Graph, query: str, doc_filter: Optional[list[UUID]] = None
) -> RAGAnswer:
  """Performs a quick search and Retrieval-Augmented Generation (RAG) using the vector database and language model.

  Args:
    query (str): The input string to search for relevant attributes in the graph.
    graph (Graph): The graph on which the quick search is performed.
    doc_filter: (Optional[list[UUID]]) The optional list of document id's to filter for.

  Returns:
    RAGAnswer: An object containing the answer, sources, and any visual metadata.
  """
  # Retrieve and rank attributes based on the query
  if query.strip() == "":
    return RAGAnswer(answer="please ask a question", sources=None, visuals=None)

  attributes: list[AttributeSearch] = get_attributes_search(graph, query, doc_filter)
  chunks_string: str = ""

  if len(attributes) == 0:
    chunks_string = "Nothing found in the graph regarding this question!"
  else:
    for a in attributes:
      chunks_string += a.text + "\n"

  prompt: str = process_template(
    RAG_SEARCH, data={"CONTEXT": chunks_string, "QUERY": query}
  )

  answer: str | None = graph.model.get_plain_response(prompt)

  # TODO: add the visuals in future PR
  # visuals: list[MetadataVisual] = choose_suitable_visuals(graph, attributes)
  visuals: list[MetadataVisual] = []
  # Create the RAGAnswer object
  rag_answer = RAGAnswer(
    answer=answer if answer else "Something went wrong with generating the answer",
    sources=attributes,
    visuals=visuals if visuals else None,
  )

  return rag_answer


def choose_suitable_visuals(
  graph: Graph, attributes: list[AttributeSearch]
) -> list[Node]:
  """Identify and select unique visual nodes from a graph based on provided attributes.

  This function iterates through a list of attributes, checking for visual metadata in each attribute's metadata.
  It collects nodes from the graph that are marked as visual and belong to the same document as the attribute's parent nodes.

  Args:
    graph (Graph): The graph object containing the nodes and their metadata.
    attributes (list[AttributeSearch]): A list of attributes to be used for filtering visual nodes.
                                          Each attribute should have metadata that may include visual metadata and parent nodes.

  Returns:
    list[Node]: A list of unique visual nodes that match the given attributes. The nodes are returned in the form of a list.
  """
  unique_visual_nodes: set[Node] = set()

  for attr in attributes:
    if not attr.metadata:
      continue

    item = list(attr.metadata)[0]
    # Only handle attributes with visuals
    if not item.visual_metadata:
      continue

    for p_node in attr.parent_nodes:
      node: Node | None = graph.repository.get_node_by_name(
        p_node, document_id=item.document_id
      )
      if not node:
        continue
      if node.is_visual:
        unique_visual_nodes.add(node)

  return list(unique_visual_nodes)


def get_attributes_search(
  graph: Graph, query: str, doc_filter: Optional[list[UUID]] = None
) -> list[AttributeSearch]:
  """Gets and ranks all relevant objects in the graph based on the query.

  Args:
    query (str): The input query used to search and rank attributes.
    graph (Graph): The graph on which the quick search is performed.
    doc_filter: (Optional[list[UUID]]) The optional list of document id's to filter for.

  Returns:
    list[AttributeSearch]: A list of AttributeSearch objects representing the ranked attributes relevant to the query.
  """
  # Initialize search metadata for attributes
  search_metadata: dict[str, Any] = {"level": 0}

  if doc_filter:
    search_metadata["document_id"] = [str(id) for id in doc_filter]

  # Perform the final search for attributes
  attributes_results: list[VectorSearchResult] = graph.vector_db.search(
    query=query,
    top_n=40,
    metadata=search_metadata,
    collection_name=MAIN_COLLECTION,
  )

  # Filter and reformat the reranked attributes before returning them
  return rerank_and_filter_attributes(graph, query, attributes_results, threshold=0.1)


def rerank_and_filter_attributes(
  graph: Graph,
  query: str,
  attributes_results: list[VectorSearchResult],
  threshold: float = 0.2,
) -> list[AttributeSearch]:
  """Filters and reformats a list of reranked attributes based on relevance score.

  Args:
    graph (Graph): The graph.
    query (str): The question to find an answer for.
    attributes_results (list[VectorSearchResult]):
      A list with attribute resulst from the vector search.
    threshold (float): The reranker threshold.

  Returns:
    list[AttributeSearch]: A list of AttributeSearch objects that have been filtered by relevance
    score and enriched with the corresponding metadata and parent nodes.
  """
  attributes_string: list[str] = [r.chunk for r in attributes_results]
  chunk_results: dict[str, VectorSearchResult] = {
    r.chunk: r for r in attributes_results
  }

  # Rerank the retrieved results
  reranked_attributes: list[RerankerResult] = graph.reranker.rerank(
    query, attributes_string, top_n=len(attributes_string)
  )

  return filter_attributes(graph, reranked_attributes, chunk_results, threshold)


def filter_attributes(
  graph: Graph,
  reranked_attributes: list[RerankerResult],
  chunk_results: dict[str, VectorSearchResult],
  threshold: float,
) -> list[AttributeSearch]:
  """Filters reranked attributes based on relevance score and retrieves associated metadata.

  Args:
    graph (Graph): The graph holding the repository.
    reranked_attributes (list[RerankerResult]): A list of reranked attributes.
    chunk_results (dict[str, VectorSearchResult]): The vector search result mapped to its text.
    threshold (float): The relevance score threshold for filtering.

  Returns:
    list[AttributeSearch]: A list of filtered and enriched AttributeSearch objects.
  """
  filtered_attributes = []

  for r in reranked_attributes:
    if r.relevance_score <= threshold:
      break

    search_result: VectorSearchResult | None = chunk_results.get(r.text)
    if search_result:
      attribute = create_attribute_search(graph, r.text, search_result)
      if attribute:
        filtered_attributes.append(attribute)

  return filtered_attributes


def create_attribute_search(
  graph: Graph, text: str, search_result: VectorSearchResult
) -> AttributeSearch:
  """Creates an AttributeSearch object based on the metadata and graph nodes or edges.

  Args:
    graph (Graph): The graph holding the repository.
    text (str): The attribute text (chunk).
    search_result (VectorSearchResult): The vector search result for the object.

  Returns:
    AttributeSearch | None: The constructed AttributeSearch object or None if no valid data.
  """
  metadata_obj, parent_nodes = None, []
  if search_result.type == "node":
    node = graph.repository.get_node_by_id(search_result.id)
    if node:
      metadata_obj = node.metadata
      parent_nodes = [node.name]

  elif search_result.type == "edge":
    edge = graph.repository.get_edge_by_id(search_result.id)
    if edge:
      metadata_obj = edge.metadata
      parent_nodes = [edge.to.name, edge.frm.name]

  elif search_result.type == "property":
    prop = graph.repository.get_property_by_id(search_result.id)
    if prop:
      metadata_obj = prop.metadata
      parent_nodes = [prop.node.name]

  return AttributeSearch(text=text, metadata=metadata_obj, parent_nodes=parent_nodes)
