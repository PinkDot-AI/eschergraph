from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class Embedding(ABC):
  """The abstract base class for all the embedding models used in the package."""

  @abstractmethod
  def get_embedding(self, list_text: list[str]) -> list[list[float]]:
    """Get the embedding vectors for a list of text."""
    raise NotImplementedError
