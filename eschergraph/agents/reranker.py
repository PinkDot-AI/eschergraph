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
  """The abstract base class for all rerankers used in the package."""

  required_credentials: list[str]

  @abstractmethod
  def rerank(
    self, query: str, text_list: list[str], top_n: int
  ) -> list[RerankerResult]:
    """Rerank the search results based on relevance for the query.

    Args:
      query (str): The query to search for.
      text_list (list[str]): The results to rerank.
      top_n (int): The number of results to return.

    Returns:
      A list of reranked results.
    """
    raise NotImplementedError

  def get_model_name(self) -> str:
    """Returns the models name."""
    raise NotImplementedError
