from __future__ import annotations

from unittest.mock import patch
from uuid import UUID
from uuid import uuid4

from eschergraph.config import MAIN_COLLECTION
from eschergraph.graph.graph import Graph
from eschergraph.graph.search.global_search import AttributeSearch
from eschergraph.graph.search.global_search import get_relevant_extractions
from eschergraph.graph.search.global_search import global_search


def test_global_search(graph_unit: Graph) -> None:
  query = "test query"
  context = "Attribute 1\nAttribute 2"
  full_prompt = "Processed template with context and query"

  with patch(
    "eschergraph.graph.search.global_search.get_relevant_extractions"
  ) as mock_get_extractions:
    with patch(
      "eschergraph.graph.search.global_search.process_template"
    ) as mock_process_template:
      mock_get_extractions.return_value = [
        AttributeSearch(text="Attribute 1", metadata=None, parent_nodes=[""]),
        AttributeSearch(text="Attribute 2", metadata=None, parent_nodes=[""]),
      ]
      mock_process_template.return_value = full_prompt
      graph_unit.model.get_plain_response.return_value = "Generated answer"

      result = global_search(graph_unit, query)

      assert result == "Generated answer"
      mock_get_extractions.assert_called_once_with(graph_unit, query, None)
      mock_process_template.assert_called_once_with(
        "search/global_search_context.jinja", {"CONTEXT": context, "QUERY": query}
      )
      graph_unit.model.get_plain_response.assert_called_once_with(full_prompt)


def test_global_search_get_relevant_extractions(graph_unit: Graph) -> None:
  prompt = "test prompt"
  search_results = [
    {"chunk": "Chunk 1", "metadata": {"level": 1}},
    {"chunk": "Chunk 2", "metadata": {"level": 1}},
    {
      "chunk": 123,
      "metadata": {"level": 1},
    },  # This should be filtered out as it's not a string
  ]
  reranked_results = [
    AttributeSearch(text="Reranked Chunk 1", metadata=None, parent_nodes=[""]),
    AttributeSearch(text="Reranked Chunk 2", metadata=None, parent_nodes=[""]),
  ]

  with patch(
    "eschergraph.graph.search.global_search.rerank_and_filter_attributes",
    return_value=reranked_results,
  ):
    graph_unit.vector_db.search.return_value = search_results

    get_relevant_extractions(graph_unit, prompt)

    graph_unit.vector_db.search.assert_called_once_with(
      query=prompt, top_n=15, metadata={"level": 1}, collection_name=MAIN_COLLECTION
    )


def test_global_search_with_doc_filter(graph_unit: Graph) -> None:
  doc_filter: list[UUID] = [uuid4() for _ in range(10)]

  global_search(graph_unit, "test_query", doc_filter=doc_filter)

  graph_unit.vector_db.search.assert_called_once_with(
    query="test_query",
    top_n=15,
    metadata={"level": 1, "document_id": [str(id) for id in doc_filter]},
    collection_name=MAIN_COLLECTION,
  )


def test_global_search_without_doc_filter(graph_unit: Graph) -> None:
  global_search(graph_unit, "test_query")

  graph_unit.vector_db.search.assert_called_once_with(
    query="test_query", top_n=15, metadata={"level": 1}, collection_name=MAIN_COLLECTION
  )
