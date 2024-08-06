from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class VectorDB(ABC):
  """This is the Abstrcat class for all vector DB implementations."""

  @abstractmethod
  def connect(self) -> None:
    """Possible conntection class."""
    pass

  @abstractmethod
  def create_collection(self, name: str) -> None:
    """Crete a collection with a given name.

    Parameters:
    name (str) name for the collection.
    """
    pass

  @abstractmethod
  def input_documents(
    self,
    embeddings: list[list[float]],
    documents: list[str],
    ids: list[str],
    metadata: list[dict[str, str]],
    collection_name: str,
  ) -> None:
    """Store documents with their embeddings, ids, and metadata.

    Parameters:
    embedding (List[List[float]]): List of embeddings for the documents.
    document (List[str]): List of document texts.
    ids (List[int]): List of document IDs.
    metadata (List[Dict[str, Any]]): List of metadata dictionaries.
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

    Parameters:
    embedding (List[float]): Embedding of the query document.
    top_n (int): Number of top documents to retrieve.
    metadata (Dict[str, Any]): Metadata to filter the search results.

    Returns:
    List[Dict[str, Any]]: List of documents that match the query.
    """
    pass
