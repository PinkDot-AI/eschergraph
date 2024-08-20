from __future__ import annotations
from typing import Dict, List

import chromadb
from chromadb import Collection
from chromadb import QueryResult
from chromadb.api import ClientAPI

from eschergraph.graph.persistence.vector_db.vector_db import VectorDB


class ChromaDB(VectorDB):
  """The ChromaDB vector database implementation."""

  def __init__(self) -> None:
    """Initialize the ChromaDB client."""
    self.client: ClientAPI = chromadb.Client()

  def create_collection(self, name: str) -> None:
    """Create a new collection in ChromaDB.

    Args:
        name (str): The name of the collection to be created.
    """
    self.collection: Collection = self.client.create_collection(name=name)

  def insert(
    self,
    embeddings: list[list[float]],
    documents: list[str],
    ids: list[str],
    metadata: list[dict[str, str]],
    collection_name: str,
  ) -> None:
    """Input documents into a ChromaDB collection.

    Args:
      embeddings (list[list[float]]): List of embeddings for the documents.
      documents (list[str]): List of documents to be added.
      ids (list[str]): List of IDs corresponding to each document.
      metadata (list[dict]): List of metadata dictionaries for each document.
      collection_name (str): Name of the collection to add documents to.
    """
    collection: Collection = self.client.get_collection(name=collection_name)
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
    metadata: dict[str, str],
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
    collection: Collection = self.client.get_collection(name=collection_name)
    result: QueryResult = collection.query(
      query_embeddings=[embedding],
      n_results=top_n,
      where=metadata,
      include=["documents"],
    )

    return result  # type: ignore

  def format_search_results(
    result: QueryResult,
  ) -> List[Dict[str, int | str | float | dict]]:
    """Format search results into a standard.

    Args:
        result (QueryResult): The result of a search

    Returns:
        Dict[str, int | str | float | dict]: A list of dictionaries containing standardized format
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
