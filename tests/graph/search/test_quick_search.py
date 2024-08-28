from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.providers.openai import ModelProvider
from eschergraph.agents.reranker import RerankerResult
from eschergraph.graph.persistence.metadata import Metadata
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB
from eschergraph.graph.search.quick_search import _get_attributes
from eschergraph.graph.search.quick_search import AttributeSearch
from eschergraph.graph.search.quick_search import quick_search
from eschergraph.graph.search.quick_search import rerank_and_filter_attributes


def test_quick_search() -> None:
  # Mocking the vector database and model provider
  vector_db_mock = MagicMock(spec=VectorDB)
  model_mock = MagicMock(spec=ModelProvider)
  RAG_SEARCH = "search/rag_prompt.jinja"

  # Test input query
  test_query = "when was google founded?"

  # Case 1: Empty query string
  result = quick_search(vector_db_mock, "", model_mock)
  assert (
    result == "please ask a question"
  ), "Empty query should return a prompt message."

  # Mock the _get_attributes function
  with patch(
    "eschergraph.graph.search.quick_search._get_attributes"
  ) as mock_get_attributes:
    # Case 2: No attributes found
    mock_get_attributes.return_value = []

    # Mock model.get_plain_response
    model_mock.get_plain_response.return_value = (
      "Nothing found in the graph regarding this question!"
    )

    # Call the function under test
    result = quick_search(vector_db_mock, test_query, model_mock)

    # Assert the expected result when no attributes are found
    assert result == "Nothing found in the graph regarding this question!"

    # Case 3: Attributes found
    mock_get_attributes.return_value = [
      AttributeSearch(
        text="Google was founded in 1998.", metadata=None, parent_node=""
      ),
      AttributeSearch(
        text="Headquarters in Mountain View.", metadata=None, parent_node=""
      ),
    ]

    # No need to mock process_template, it's being used directly as per the code.
    model_mock.get_plain_response.return_value = (
      "Google was founded in 1998 and is headquartered in Mountain View."
    )

    # Call the function under test
    result = quick_search(vector_db_mock, test_query, model_mock)

    # Expected chunks_string in the generated prompt
    expected_chunks_string = (
      "Google was founded in 1998.\nHeadquarters in Mountain View.\n"
    )

    # Manually process the template (as done in the function)
    expected_prompt = process_template(
      RAG_SEARCH, data={"chunks": expected_chunks_string, "query": test_query}
    )

    # Assert that the function returns the expected model response
    assert result == "Google was founded in 1998 and is headquartered in Mountain View."

    assert model_mock.get_plain_response.call_count == 2

    # Check if the expected prompt was passed in one of the calls
    model_mock.get_plain_response.assert_any_call(expected_prompt)


def test_get_attributes() -> None:
  # Mocking the vector database and model provider
  vector_db_mock = MagicMock(spec=VectorDB)
  model_mock = MagicMock(spec=ModelProvider)

  test_query = "when was google founded?"
  collection_name = "test_collection"

  # Mock the extract_entities_from return value
  with patch(
    "eschergraph.graph.search.quick_search.extract_entities_from",
    return_value=["google"],
  ):
    # Mock vector_db.search and format_search_results behavior
    vector_db_mock.search.side_effect = [
      [
        {"chunk": "google", "metadata": {"type": "node"}},
        {"chunk": "other_entity", "metadata": {"type": "node"}},
      ],  # Search result for extracted nodes
      [
        {"chunk": "founded in 1998", "metadata": {"type": "property"}},
        {"chunk": "HQ in Mountain View", "metadata": {"type": "property"}},
      ],  # Search result for attributes
    ]

    vector_db_mock.format_search_results.side_effect = (
      lambda x: x
    )  # Directly return input

    # Mock the rerank_and_filter_attributes function
    with patch(
      "eschergraph.graph.search.quick_search.rerank_and_filter_attributes"
    ) as mock_rerank_and_filter:
      mock_rerank_and_filter.return_value = ["founded in 1998"]

      # Call the function under test
      attributes = _get_attributes(
        vector_db=vector_db_mock,
        query=test_query,
        model=model_mock,
        collection_name=collection_name,
      )

      # Assert the reranked and filtered attributes were called correctly
      mock_rerank_and_filter.assert_called_once_with(
        test_query,
        ["founded in 1998", "HQ in Mountain View"],
        [
          {"chunk": "founded in 1998", "metadata": {"type": "property"}},
          {"chunk": "HQ in Mountain View", "metadata": {"type": "property"}},
        ],
      )

      # Assert the returned attributes are correct
      assert attributes == ["founded in 1998"]


def test_rerank_and_filter_attributes() -> None:
  test_query = "when was google founded?"

  # Test input for attributes_string and attributes_results
  attributes_string = ["founded in 1998", "HQ in Mountain View"]
  attributes_results = [
    {
      "chunk": "founded in 1998",
      "metadata": {"document_id": "doc1", "chunk_id": "chunk1", "type": "property"},
    },
    {
      "chunk": "HQ in Mountain View",
      "metadata": {"document_id": "doc2", "chunk_id": "chunk2", "type": "property"},
    },
  ]

  # Mock the rerank function
  with patch("eschergraph.graph.search.quick_search.rerank") as mock_rerank:
    # Rerank result with relevance scores
    mock_rerank.return_value = [
      RerankerResult(text="founded in 1998", relevance_score=0.25, index=1),
      RerankerResult(text="HQ in Mountain View", relevance_score=0.15, index=2),
    ]

    # Call the function under test
    result = rerank_and_filter_attributes(
      test_query, attributes_string, attributes_results
    )

    # Expected output
    expected_result = [
      AttributeSearch(
        text="founded in 1998",
        metadata=Metadata(document_id="doc1", chunk_id="chunk1"),
        parent_node="",
      )
    ]

    # Verify that the rerank function was called with the correct arguments
    mock_rerank.assert_called_once_with(
      test_query, attributes_string, top_n=len(attributes_string)
    )

    # Assert that the result matches the expected filtered and formatted attributes
    assert result == expected_result
