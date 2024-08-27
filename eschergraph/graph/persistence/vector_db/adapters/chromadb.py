from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from uuid import UUID

import chromadb

from eschergraph.agents.embedding import Embedding
from eschergraph.agents.embedding import get_embedding_model
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB


class ChromaDB(VectorDB):
  """This is the ChromaDB implementation."""

  def __init__(self) -> None:
    """Initialize the ChromaDB client."""
    self.client = chromadb.Client()
    self.embedding_model: Embedding = get_embedding_model()

  def connect(self) -> None:
    """Connect to ChromaDB. Currently not used."""
    ...

  def get_or_create_collection(self, collection_name: str) -> None:
    """Create a new collection in ChromaDB.

    Args:
      collection_name (str): The name of the collection to be created.
    """
    self.collection = self.client.get_or_create_collection(name=collection_name)

  def insert(
    self,
    documents: list[str],
    ids: list[UUID],
    metadata: list[dict[str, str]],
    collection_name: str,
  ) -> None:
    """Insert documents into a ChromaDB collection.

    Args:
      documents (list[str]): List of documents to be added.
      ids (list[str]): List of IDs corresponding to each document.
      metadata (list[dict]): List of metadata dictionaries for each document.
      collection_name (str): Name of the collection to add documents to.
    """
    collection = self.client.get_collection(name=collection_name)
    embeddings = self.embedding_model.get_embedding(list_text=documents)
    ids: list[str] = [str(id) for id in ids]
    collection.add(
      documents=documents,
      ids=ids,
      embeddings=embeddings,
      metadatas=metadata,
    )

  def search(
    self,
    query: str,
    top_n: int,
    metadata: dict[str, Any],
    collection_name: str,
  ) -> dict[str, str]:
    """Search for documents in a ChromaDB collection.

    Args:
      query (list[float]): The query to search for.
      top_n (int): The number of top results to return.
      metadata (dict): Metadata to filter the search results.
      collection_name (str): Name of the collection to search in.

    Returns:
      dict: Search results containing the documents.
    """
    embedding = self.embedding_model.get_embedding([query])
    collection = self.client.get_collection(name=collection_name)
    results: dict[str, str] = collection.query(
      query_embeddings=embedding,
      n_results=top_n,
      where=metadata,
      include=["documents", "metadatas", "distances"],
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

  def delete_with_id(self, ids: list[UUID], collection_name: str) -> None:
    """Deletes records from a specified collection using their unique IDs.

    Args:
        ids (list[str]): A list of unique identifiers corresponding to the records to be deleted.
        collection_name (str): The name of the collection from which the records will be deleted.
    """
    collection = self.client.get_collection(name=collection_name)
    ids: list[str] = [str(id) for id in ids]
    collection.delete(ids=ids)

  def delete_with_metadata(
    self, metadata: Dict[str, Any], collection_name: str
  ) -> None:
    """Delete an item in the vectordb by metadata filters.

    Args:
      metadata (dict[str, str]): Metadata to filter the search results.
      collection_name (str): The name of the collection.
    """
    raise NotImplementedError
