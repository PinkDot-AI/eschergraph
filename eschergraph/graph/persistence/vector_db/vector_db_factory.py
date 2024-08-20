from __future__ import annotations

from eschergraph.graph.persistence.vector_db.providers.chromadb import ChromaDB
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB


def get_vector_db(db_type: str) -> VectorDB:
  """Factory method to get the appropriate vector database instance.

  Parameters:
  db_type (str): Type of the vector database (e.g., 'specific_db1', 'specific_db2').

  Returns:
  VectorDBBase: An instance of a subclass of VectorDBBase.
  """
  if db_type == "chroma_db":
    return ChromaDB()
  else:
    raise ValueError(f"Unknown vector database type: {db_type}")
