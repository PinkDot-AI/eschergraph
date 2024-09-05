from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
from uuid import UUID

import pytest

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.reranker import Reranker
from eschergraph.graph.graph import Graph
from eschergraph.graph.search.quick_search import _get_attributes
from eschergraph.graph.search.quick_search import AttributeSearch
from eschergraph.graph.search.quick_search import quick_search
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes

RAG_SEARCH = "search/question_with_context.jinja"


def test_quick_search(graph_unit: Graph) -> None:
  # Test case 1: Empty query
  assert quick_search(graph_unit, "") == "please ask a question"

  # Test case 2: No attributes found
  with patch("eschergraph.graph.search.quick_search._get_attributes", return_value=[]):
    graph_unit.model.get_plain_response.return_value = "No results found"

    result = quick_search(graph_unit, "test query")
    assert result == "No results found"
    graph_unit.model.get_plain_response.assert_called_with(
      process_template(
        RAG_SEARCH,
        data={
          "CONTEXT": "Nothing found in the graph regarding this question!",
          "QUERY": "test query",
        },
      )
    )

  # Test case 3: Attributes found and answer generated
  attributes = [
    AttributeSearch(text="Attribute 1", metadata=None, parent_nodes=[""]),
    AttributeSearch(text="Attribute 2", metadata=None, parent_nodes=[""]),
  ]
  with patch(
    "eschergraph.graph.search.quick_search._get_attributes", return_value=attributes
  ):
    graph_unit.model.get_plain_response.return_value = "Generated answer"

    result = quick_search(graph_unit, "test query with attributes")
    assert result == "Generated answer"
    graph_unit.model.get_plain_response.assert_called_with(
      process_template(
        RAG_SEARCH,
        data={
          "CONTEXT": "Attribute 1\nAttribute 2\n",
          "QUERY": "test query with attributes",
        },
      )
    )

  # Test case 4: Attributes found but answer generation fails
  with patch(
    "eschergraph.graph.search.quick_search._get_attributes", return_value=attributes
  ):
    graph_unit.model.get_plain_response.return_value = None

    result = quick_search(graph_unit, "test query with failed generation")
    assert result == "Something went wrong with generating the answer"


@pytest.mark.usefixtures("graph_unit")
def test_get_attributes(graph_unit: Graph) -> None:
  query = "Find attributes for node"

  # Mock the VectorDB search and format results
  search_results_nodes = [{"chunk": "node1"}, {"chunk": "node2"}]
  search_results_attributes = [
    {"chunk": "attribute 1", "metadata": {"entity1": "node1"}},
    {"chunk": "attribute 2", "metadata": {"entity2": "node2"}},
  ]

  # Mock the graph's vector_db search and format_search_results methods
  graph_unit.vector_db.search = MagicMock()  # type: ignore
  graph_unit.vector_db.format_search_results.side_effect = [
    search_results_nodes,  # First search for nodes
    search_results_attributes,  # Second search for attributes
  ]

  # Mock rerank_and_filter_attributes to return filtered attributes
  filtered_attributes = [
    AttributeSearch(text="attribute 1", metadata=None, parent_nodes=[""]),
    AttributeSearch(text="attribute 2", metadata=None, parent_nodes=[""]),
  ]
  with patch(
    "eschergraph.graph.search.quick_search.rerank_and_filter_attributes",
    return_value=filtered_attributes,
  ):
    # Call the function under test
    result = _get_attributes(graph=graph_unit, query=query)

    # Assertions
    assert len(result) == 2
    assert result[0].text == "attribute 1"
    assert result[1].text == "attribute 2"

    # Ensure vector_db.search was called for attributes
    graph_unit.vector_db.search.assert_any_call(
      query=query,
      top_n=40,
      metadata={"level": 0},
      collection_name="main_collection",
    )


# Test for rerank_and_filter_attributes with no attributes
@patch("eschergraph.graph.search.quick_search.rerank")
@patch("eschergraph.graph.search.quick_search.filter_attributes")
def test_rerank_and_filter_no_attributes(
  mock_filter_attributes: list[dict[str, UUID | int | str | float | dict[str, Any]]],
  mock_rerank: Reranker,
) -> None:
  graph: Graph = Mock(spec=Graph)  # Mock the graph object
  mock_filter_attributes.return_value = []

  result: list[AttributeSearch] = rerank_and_filter_attributes(graph, "test query", [])

  mock_rerank.assert_called_once()
  mock_filter_attributes.assert_called_once()
  assert result == [], "Expected empty result when no attributes are passed"


# Test for rerank_and_filter_attributes with some attributes, but none pass the threshold
@patch("eschergraph.graph.search.quick_search.rerank")
@patch("eschergraph.graph.search.quick_search.filter_attributes")
def test_rerank_and_filter_below_threshold(
  mock_filter_attributes: list[dict[str, UUID | int | str | float | dict[str, Any]]],
  mock_rerank: Reranker,
) -> None:
  graph: Graph = Mock(spec=Graph)

  attributes_results: list[dict[str, UUID | int | str | float | dict[str, Any]]] = [
    {
      "chunk": "attribute 1",
      "metadata": {"type": "node"},
      "id": "00000000-0000-0000-0000-000000000001",
    },
    {
      "chunk": "attribute 2",
      "metadata": {"type": "edge"},
      "id": "00000000-0000-0000-0000-000000000002",
    },
  ]

  mock_rerank.return_value = [
    Mock(text="attribute 1", relevance_score=0.1),
    Mock(text="attribute 2", relevance_score=0.05),
  ]

  mock_filter_attributes.return_value = []

  result: list[AttributeSearch] = rerank_and_filter_attributes(
    graph, "test query", attributes_results, threshold=0.2
  )

  mock_rerank.assert_called_once_with(
    "test query", ["attribute 1", "attribute 2"], top_n=2
  )
  mock_filter_attributes.assert_called_once()
  assert result == [], "Expected empty result when all attributes are below threshold"


# Test for rerank_and_filter_attributes with attributes passing the threshold
@patch("eschergraph.graph.search.quick_search.rerank")
@patch("eschergraph.graph.search.quick_search.filter_attributes")
def test_rerank_and_filter_above_threshold(
  mock_filter_attributes: list[dict[str, UUID | int | str | float | dict[str, Any]]],
  mock_rerank: Reranker,
) -> None:
  graph = Mock()

  attributes_results: list[dict[str, UUID | int | str | float | dict[str, Any]]] = [
    {
      "chunk": "attribute 1",
      "id": "00000000-0000-0000-0000-000000000001",
      "metadata": {"type": "node"},
    },
    {
      "chunk": "attribute 2",
      "id": "00000000-0000-0000-0000-000000000002",
      "metadata": {"type": "edge"},
    },
  ]

  reranked_results: list[Mock] = [
    Mock(text="attribute 1", relevance_score=0.3),
    Mock(text="attribute 2", relevance_score=0.25),
  ]

  mock_rerank.return_value = reranked_results
  mock_filter_attributes.return_value = [
    Mock(text="attribute 1", metadata="metadata1", parent_nodes=["Node A"]),
    Mock(text="attribute 2", metadata="metadata2", parent_nodes=["Node B", "Node C"]),
  ]

  result = rerank_and_filter_attributes(
    graph, "test query", attributes_results, threshold=0.2
  )

  mock_rerank.assert_called_once_with(
    "test query", ["attribute 1", "attribute 2"], top_n=2
  )
  mock_filter_attributes.assert_called_once()

  assert len(result) == 2, "Expected two attributes in the result"
  assert result[0].text == "attribute 1", "Expected 'attribute 1' in the result"
  assert result[1].text == "attribute 2", "Expected 'attribute 2' in the result"
