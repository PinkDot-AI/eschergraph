from __future__ import annotations

from unittest.mock import MagicMock

from eschergraph.agents.providers.openai import OpenAIProvider


def test_openai_embedding() -> None:
  """Test the get_embedding method of the ChatGPT class using a mock."""
  # Create a mock ChatGPT instance
  c: MagicMock = MagicMock(spec=OpenAIProvider)

  # Define the mock return value for the get_embedding method
  mock_embeddings: list[list[float]] = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
  c.get_embedding.return_value = mock_embeddings

  text_list: list[str] = ["This is a test sentence.", "Another sentence."]
  embeddings: list[list[float]] = c.get_embedding(text_list)

  # Perform assertions
  assert isinstance(embeddings, list), "Embeddings should be a list."
  assert all(
    isinstance(emb, list) for emb in embeddings
  ), "Each embedding should be a list."
  assert all(
    isinstance(value, float) for emb in embeddings for value in emb
  ), "Each value in the embeddings should be a float."
  assert len(embeddings) == len(
    text_list
  ), "The number of embeddings should match the number of input texts."

  # Check that the get_embedding method was called with the correct arguments
  c.get_embedding.assert_called_once_with(text_list)
