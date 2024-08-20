from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class Embedding(ABC):
  """The abstract base class for all the embedding models used in the package."""

  @abstractmethod
  def get_embedding(self, list_text: list[str]) -> list[list[float]] | None:
    """Get a list of texts to be embedded by an embedding model."""
    raise NotImplementedError
