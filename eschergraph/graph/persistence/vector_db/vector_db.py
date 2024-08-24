from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from uuid import UUID


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
    embeddings: List[List[float]],
    documents: List[str],
    ids: List[str],
    metadata: List[Dict[str, str]],
    collection_name: str,
  ) -> None:
    """Store documents with their embeddings, ids, and metadata.

    Args:
      embeddings (List[List[float]]): List of embeddings for the documents.
      documents (List[str]): List of document texts.
      ids (List[int]): List of document IDs.
      metadata (List[dict[str, Any]]): List of metadata dictionaries.
      collection_name (str): The name of the collection.
    """
    pass

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
      metadata (dict[str, str]): Metadata to filter the search results.
      collection_name (str): The collection's name.

    Returns:
      dict[str, str]: List of documents that match the query.
    """
    pass

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
    pass

  @abstractmethod
  def delete_with_metadata(
    self,
    metadata: Dict[str, Any],
    collection_name: str,
  ) -> None:
    """Delete an item in the vectordb by metadata filters.

    Args:
      metadata (dict[str, str]): Metadata to filter the search results.
      collection_name (str): The name of the collection.
    """
    pass

  @abstractmethod
  def delete_with_id(
    self,
    ids: list[str],
    collection_name: str,
  ) -> None:
    """Delete an item in the vectordb by its id.

    Args:
      ids (str): list of ids that need to be removed
      collection_name (str): The name of the collection.
    """
    pass
