from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Optional
from uuid import UUID

from eschergraph.persistence.vector_db.vector_search_result import VectorSearchResult


class VectorDB(ABC):
  """This is the abstract base class for all vector DB implementations.

  It is important to note that an embedding model is included in the abstract vector database class.
  """

  required_credentials: list[str]

  @abstractmethod
  def connect(self) -> None:
    """Possible connection method."""
    raise NotImplementedError

  @abstractmethod
  def insert(
    self,
    documents: list[str],
    ids: list[UUID],
    metadata: list[dict[str, str | int]],
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
    raise NotImplementedError

  @abstractmethod
  def search(
    self,
    query: str,
    top_n: int,
    collection_name: str,
    metadata: Optional[dict[str, str | int]] = None,
  ) -> list[VectorSearchResult]:
    """Search for the top_n documents that are most similar to the given query.

    Args:
      query (str): The query to search for.
      top_n (int): Number of top search results to retrieve.
      collection_name (str): The name of the collection.
      metadata (Optional[dict[str, str | int]]): Metadata to filter the search results.

    Returns:
      A list of vector search results.
    """
    raise NotImplementedError

  @abstractmethod
  def delete_by_ids(
    self,
    ids: list[UUID],
    collection_name: str,
  ) -> None:
    """Delete records from collection by their ids.

    Args:
      ids (list[str]): list of ids that need to be removed
      collection_name (str): The name of the collection.
    """
    raise NotImplementedError
