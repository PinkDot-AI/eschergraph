from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from attrs import define


@define
class RerankerResult:
  """Represents a reranked item with its index, relevance score, and associated text.

  Attributes:
      index (int): The position of the item in the original list.
      relevance_score (float): The relevance score assigned by the reranker.
      text (str): The content of the item.
  """

  index: int
  relevance_score: float
  text: str


class Reranker(ABC):
  """The abstract base class for all the embedding models used in the package."""

  @abstractmethod
  def rerank(
    self, query: str, texts_list: list[str], top_n: int
  ) -> list[RerankerResult]:
    """Get a list of texts to be embedded by an embedding model."""
    raise NotImplementedError
