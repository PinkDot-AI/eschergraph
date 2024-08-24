from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from uuid import UUID

import chromadb

from eschergraph.graph.persistence.vector_db.vector_db import VectorDB


class ChromaDB(VectorDB):
  """This is the ChromaDB implementation."""

  def __init__(self) -> None:
    """Initialize the ChromaDB client."""
    self.client = chromadb.Client()

  def connect(self) -> None:
    """Connect to ChromaDB. Currently a placeholder function."""
    pass

  def create_collection(self, name: str) -> None:
    """Create a new collection in ChromaDB.

    Args:
      name (str): The name of the collection to be created.
    """
    self.collection = self.client.create_collection(name=name)

  def insert_documents(
    self,
    embeddings: list[list[float]],
    documents: list[str],
    ids: list[str],
    metadata: list[dict[str, str]],
    collection_name: str,
  ) -> None:
    """Insert documents into a ChromaDB collection.

    Args:
      embeddings (list[list[float]]): List of embeddings for the documents.
      documents (list[str]): List of documents to be added.
      ids (list[str]): List of IDs corresponding to each document.
      metadata (list[dict]): List of metadata dictionaries for each document.
      collection_name (str): Name of the collection to add documents to.
    """
    collection = self.client.get_collection(name=collection_name)
    collection.add(
      documents=documents,
      ids=ids,
      embeddings=embeddings,
      metadatas=metadata,
    )

  def search(
    self,
    embedding: list[float],
    top_n: int,
    metadata: dict[str, Any],
    collection_name: str,
  ) -> dict[str, str]:
    """Search for documents in a ChromaDB collection.

    Args:
      embedding (list[float]): The embedding to search for.
      top_n (int): The number of top results to return.
      metadata (dict): Metadata to filter the search results.
      collection_name (str): Name of the collection to search in.

    Returns:
      dict: Search results containing the documents.
    """
    collection = self.client.get_collection(name=collection_name)
    results: dict[str, str] = collection.query(
      query_embeddings=[embedding],
      n_results=top_n,
      where=metadata,
      include=["documents"],
    )

    return results

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
    return [
      {
        "id": result["ids"][0][i],
        "chunk": result["documents"][0][i],
        "distance": result["distances"][0][i],
        "metadata": result["metadatas"][0][i],
      }
      for i in range(len(result["ids"][0]))
    ]

  def delete_with_id(self, ids: list[str], collection_name: str) -> None:
    """Deletes records from a specified collection using their unique IDs.

    Args:
        ids (list[str]): A list of unique identifiers corresponding to the records to be deleted.
        collection_name (str): The name of the collection from which the records will be deleted.
    """
    collection = self.client.get_collection(name=collection_name)
    collection.delete(ids=ids)

  def delete_with_metadata(
    self, metadata: Dict[str, Any], collection_name: str
  ) -> None:
    """Deletes records from a specified collection based on metadata conditions.

    Args:
        metadata (Dict[str, Any]): A dictionary specifying the metadata conditions that must be met
                                   for the records to be deleted. The keys are metadata field names,
                                   and the values are the required values for deletion.
        collection_name (str): The name of the collection from which the records will be deleted.
    """
    collection = self.client.get_collection(name=collection_name)
    collection.delete(where=metadata)
