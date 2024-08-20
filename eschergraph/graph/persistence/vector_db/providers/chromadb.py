from __future__ import annotations

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
    collection = self.client.get_collection(name=collection_name)
    results: dict[str, str] = collection.query(
      query_embeddings=[embedding],
      n_results=top_n,
      where=metadata,
      include=["documents"],
    )

    return results