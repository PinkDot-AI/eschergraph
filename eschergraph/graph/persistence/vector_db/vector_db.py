from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class VectorDB(ABC):
  """This is the abstract base class for all vector DB implementations."""

  @abstractmethod
  def connect(self) -> None:
    """Possible connection method."""
    pass

  @abstractmethod
  def create_collection(self, name: str) -> None:
    """Create a collection with a given name.

    Args:
      name (str): Name for the collection.
    """
    pass

  @abstractmethod
  def insert_documents(
    self,
    embeddings: list[list[float]],
    documents: list[str],
    ids: list[str],
    metadata: list[dict[str, str]],
    collection_name: str,
  ) -> None:
    """Store documents with their embeddings, ids, and metadata.

    Args:
      embeddings (list[List[float]]): List of embeddings for the documents.
      documents (list[str]): List of document texts.
      ids (list[int]): List of document IDs.
      metadata (list[dict[str, Any]]): List of metadata dictionaries.
      collection_name (str): The name of the collection.
    """
    pass

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
      metadata (dict[str, str]): Metadata to filter the search results.
      collection_name (str): The collection's name.

    Returns:
      dict[str, str]: List of documents that match the query.
    """
    pass
