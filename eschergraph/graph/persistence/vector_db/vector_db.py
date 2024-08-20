from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from uuid import UUID


class VectorDB(ABC):
  """The abstract base class for a vector database."""

  @abstractmethod
  def create_collection(self, name: str) -> None:
    """Create a collection with a given name.

    Args:
      name (str): Collection's name.
    """
    raise NotImplementedError

  @abstractmethod
  def insert(
    self,
    embeddings: List[List[float]],
    documents: List[str],
    ids: List[str],
    metadata: List[Dict[str, str]],
    collection_name: str,
  ) -> None:
    """Store documents with their embeddings, ids, and metadata.

    Args:
      embeddings (list[list[float]]): List of embeddings for the documents.
      documents (list[str]): List of document texts.
      ids (list[int]): List of document IDs.
      metadata (list[Dict[str, Any]]): List of metadata dictionaries.
      collection_name (str): The name of the collection.
    """
    raise NotImplementedError

  @abstractmethod
  def search(
    self,
    embedding: List[float],
    top_n: int,
    metadata: Dict[str, Any],
    collection_name: str,
  ) -> Dict[str, str]:
    """Search for the top_n documents that are most similar to the given embedding.

    Args:
      embedding (list[float]): Embedding of the query document.
      top_n (int): Number of top documents to retrieve.
      metadata (dict[str, Any]): Metadata to filter the search results.
      collection_name (str): The name of the collection.

    Returns:
      Dictionary with results that match the que
    """
    raise NotImplementedError

  @abstractmethod
  def format_search_results(
    self,
    result: Dict[str, str],
  ) -> List[Dict[str, UUID | int | str | float | Dict[str, Any]]]:
    """Format search results into a standard.

    Args:
        result: The result of a search

    Returns:
        Dict[str, int | str | float | dict]: A list of dictionaries containing a standardized format
    """
    raise NotImplementedError
