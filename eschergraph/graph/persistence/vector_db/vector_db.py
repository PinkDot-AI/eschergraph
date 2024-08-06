from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class VectorDB(ABC):
  """The abstract base class for a vector database."""

  @abstractmethod
  def create_collection(self, name: str) -> None:
    """Crete a collection with a given name.

    Args:
      name (str): Collection's name.
    """
    raise NotImplementedError

  @abstractmethod
  def insert(
    self,
    embeddings: list[list[float]],
    documents: list[str],
    ids: list[str],
    metadata: list[dict[str, str]],
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
    embedding: list[float],
    top_n: int,
    metadata: dict[str, str],
    collection_name: str,
  ) -> dict[str, str]:
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
