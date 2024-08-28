from __future__ import annotations

import os
from abc import ABC
from abc import abstractmethod

from dotenv import load_dotenv

load_dotenv()


def get_embedding_model(embedding_type: str = "text_embedding_3_large") -> Embedding:
  """Factory method to get the default embedding model openais text embedding large.

  Args:
    embedding_type (str): Type of the embedding model.

  Returns:
    An implementation of the VectorDB abstract base class.
  """
  openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

  if embedding_type == "text_embedding_3_large" and openai_api_key:
    from eschergraph.agents.providers.openai import OpenAIProvider, OpenAIModel

    return OpenAIProvider(
      model=OpenAIModel.TEXT_EMBEDDING_LARGE,
    )
  else:
    raise ValueError(f"Unknown embedding model type: {embedding_type}")


class Embedding(ABC):
  """The abstract base class for all the embedding models used in the package."""

  @abstractmethod
  def get_embedding(self, list_text: list[str]) -> list[list[float]]:
    """Get the embedding vectors for a list of text."""
    raise NotImplementedError
