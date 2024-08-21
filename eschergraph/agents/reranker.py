from abc import ABC, abstractmethod
from typing import Dict, List

from attr import field
from sentence_transformers import CrossEncoder


class Reranker(ABC):
  """The abstract base class for all rerankers used in the package."""

  model: CrossEncoder = field(default=None)

  @abstractmethod
  def rank(self, docs: list[str], query: str, top_n: int) -> List[Dict]:
    """Rank the documents based on the relevance to the query.

    Args:
        docs (list[str]): a list of strings containing information
        query (str): string of text used for comparing relevance
        top_n (int): amount of relevant results to be returned

    Returns:
        List[Dict]: A list of dicts containing the most relevant docs and their relevance scores
    """
    ...
