from __future__ import annotations

from unittest.mock import MagicMock

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.reranker import RerankerResult


def test_reranker() -> None:
  """Test the rerank method of the JinaReranker class using a mock."""
  # Create a mock JinaReranker instance
  mock_client: MagicMock = MagicMock(spec=JinaReranker)

  # Define the mock return value for the rerank method
  mock_batch_items: list[RerankerResult] = [
    RerankerResult(index=1, text="mock text", relevance_score=0.18),
    RerankerResult(index=0, text="mock text 2", relevance_score=0.3),
  ]
  mock_client.rerank.return_value = mock_batch_items

  # Define the test inputs
  query: str = "Today is an amazing day"
  text_list: list[str] = ["one", "two"]
  top_n: int = 2

  # Call the rerank method
  reranked_items: list[RerankerResult] = mock_client.rerank(query, text_list, top_n)

  # Check that the rerank method returns the correct number of items
  assert len(reranked_items) == 2

  # Verify that the reranked items match the expected mock data
  assert reranked_items[0].index == 1
  assert reranked_items[0].text == "mock text"
  assert reranked_items[0].relevance_score == 0.18

  assert reranked_items[1].index == 0
  assert reranked_items[1].text == "mock text 2"
  assert reranked_items[1].relevance_score == 0.3

  # Check that the rerank method was called with the correct arguments
  mock_client.rerank.assert_called_once_with(query, text_list, top_n)

  # If there's a need to check the exact call, we can also use
  # mock_client.rerank.assert_called_once()
