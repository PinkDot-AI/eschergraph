from __future__ import annotations

import os
from typing import Any
from typing import Optional
from uuid import UUID

import chromadb

from eschergraph.agents.embedding import Embedding
from eschergraph.agents.embedding import get_embedding_model
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB


class ChromaDB(VectorDB):
  """This is the ChromaDB implementation with a persistent client and named storage."""

  required_credentials: list[str] = ["OPENAI_API_KEY"]

  def __init__(
    self,
    save_name: str,
    storage_dir: str = "eschergraph_storage",
    persistent: bool = True,
  ) -> None:
    """Initialize the ChromaDB client and used embedding model.

    Args:
      save_name (str): The save name for the persisted vector db.
      storage_dir (str): The directory to store the persistent client data in.
      persistent (bool): Whether the vector database should be persistent.
    """
    persistence_path = os.path.join(storage_dir, f"{save_name}-vectordb")

    # Ensure the storage directory exists
    os.makedirs(persistence_path, exist_ok=True)

    if persistent:
      self.client = chromadb.PersistentClient(path=persistence_path)
    if not persistent:
      self.client = chromadb.EphemeralClient()
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
    # TODO: add more error handling / communication to operating classes
    documents = ["null" if d.strip() == "" else d for d in documents]

    try:
      embeddings = self.embedding_model.get_embedding(list_text=documents)
    except ExternalProviderException as e:
      print(f"Something went wrong generating embeddings: {e}")
      return

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
    collection_name: str,
    metadata: Optional[dict[str, Any]] = None,
  ) -> dict[str, str]:
    """Search for documents in a ChromaDB collection.

    Args:
      query (list[float]): The query to search for.
      top_n (int): The number of top results to return.
      collection_name (str): Name of the collection to search in.
      metadata (Optional[dict[str, Any]]): Optional metadata to filter by.

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
    result: dict[str, str],
  ) -> list[dict[str, UUID | int | str | float | dict[str, Any]]]:
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
    self, metadata: dict[str, Any], collection_name: str
  ) -> None:
    """Delete an item in the vectordb by metadata filters.

    Args:
      metadata (dict[str, str]): Metadata to filter the search results.
      collection_name (str): The name of the collection.
    """
    raise NotImplementedError
