from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.reranker import RerankerResult
from eschergraph.graph.search.quick_search import _get_attributes
from eschergraph.graph.search.quick_search import AttributeSearch
from eschergraph.graph.search.quick_search import extract_entities_from
from eschergraph.graph.search.quick_search import quick_search
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes

RAG_SEARCH = "search/rag_prompt.jinja"


def test_quick_search(graph_unit):
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
          "chunks": "Nothing found in the graph regarding this question!",
          "query": "test query",
        },
      )
    )

  # Test case 3: Attributes found and answer generated
  attributes = [
    AttributeSearch(text="Attribute 1", metadata=None, parent_node=""),
    AttributeSearch(text="Attribute 2", metadata=None, parent_node=""),
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
          "chunks": "Attribute 1\nAttribute 2\n",
          "query": "test query with attributes",
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
def test_get_attributes(graph_unit):
  query = "Find attributes for node"

  # Mock extract_entities_from to return a list of nodes/entities
  extracted_entities = ["node1", "node2"]
  with patch(
    "eschergraph.graph.search.quick_search.extract_entities_from",
    return_value=extracted_entities,
  ):
    # Mock the VectorDB search and format results
    search_results_nodes = [{"chunk": "node1"}, {"chunk": "node2"}]
    search_results_attributes = [
      {"chunk": "attribute 1", "metadata": {"entity1": "node1"}},
      {"chunk": "attribute 2", "metadata": {"entity2": "node2"}},
    ]

    # Mock the graph's vector_db search and format_search_results methods
    graph_unit.vector_db.search = MagicMock()
    graph_unit.vector_db.format_search_results.side_effect = [
      search_results_nodes,  # First search for nodes
      search_results_attributes,  # Second search for attributes
    ]

    # Mock rerank_and_filter_attributes to return filtered attributes
    filtered_attributes = [
      AttributeSearch(text="attribute 1", metadata=None, parent_node=""),
      AttributeSearch(text="attribute 2", metadata=None, parent_node=""),
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

      # Ensure vector_db.search was called with the extracted entities
      graph_unit.vector_db.search.assert_any_call(
        query=", ".join(extracted_entities),
        top_n=10,
        collection_name="node_name_collection",
      )

      # Ensure vector_db.search was called for attributes
      graph_unit.vector_db.search.assert_any_call(
        query=query,
        top_n=30,
        metadata={
          "$and": [
            {"level": 0},
            {
              "$or": [
                {"entity1": {"$in": extracted_entities}},
                {"entity2": {"$in": extracted_entities}},
              ]
            },
          ]
        },
        collection_name="main_collection",
      )


def test_rerank_and_filter_attributes():
  # Define the mock data for the test
  query = "Find attributes"
  attributes_string = ["attribute 1", "attribute 2", "attribute 3"]
  attributes_results = [
    {"chunk": "attribute 1", "metadata": {"entity1": "node1"}},
    {"chunk": "attribute 2", "metadata": {"entity2": "node2"}},
    {"chunk": "attribute 3", "metadata": {"entity3": "node3"}},
  ]

  # Mock reranked results from the rerank function
  reranked_results = [
    RerankerResult(text="attribute 1", relevance_score=0.9, index=1),
    RerankerResult(text="attribute 2", relevance_score=0.85, index=2),
    RerankerResult(text="attribute 3", relevance_score=0.1, index=3),
  ]

  # Patch the rerank function to return our mocked results
  with patch(
    "eschergraph.graph.search.quick_search.rerank", return_value=reranked_results
  ):
    # Call the function with a threshold that should filter out "attribute 3"
    filtered_attributes = rerank_and_filter_attributes(
      query=query,
      attributes_string=attributes_string,
      attributes_results=attributes_results,
      threshold=0.2,  # This should filter out attribute 3
    )

    # Verify the length of the filtered attributes (attribute 3 should be excluded)
    assert len(filtered_attributes) == 2

    # Verify the content of the filtered attributes
    assert filtered_attributes[0].text == "attribute 1"
    assert filtered_attributes[1].text == "attribute 2"

    # Verify that the metadata has been properly added to the result
    assert (
      filtered_attributes[0].metadata is None
    )  # Add actual metadata enrichment check if necessary
    assert filtered_attributes[1].metadata is None

    # Test if filtering based on threshold works (attribute 3 has a score of 0.1, below threshold)


# Test extract_entities_from function
def test_extract_entities_from(graph_unit):
  # Mock the LLM model's response to return some entities
  graph_unit.model.get_json_response.return_value = {"entities": ["entity1", "entity2"]}

  # Test extracting entities
  result = extract_entities_from(
    query="Tell me about entity1 and entity2", llm=graph_unit.model
  )
  assert result == ["entity1", "entity2"]
  graph_unit.model.get_json_response.assert_called()
