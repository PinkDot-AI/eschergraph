from __future__ import annotations

from eschergraph.graph.persistence.vector_db.adapters.chromadb import ChromaDB
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB


def get_vector_db(save_name: str, db_type: str = "chroma_db") -> VectorDB:
  """Factory method to get the default vector database implementation.

  Args:
    db_type (str): Type of the vector database (e.g., 'specific_db1', 'specific_db2').
    save_name (str): the save name for the persisted vector db .

  Returns:
    An implementation of the VectorDB abstract base class.
  """
  if db_type == "chroma_db":
    return ChromaDB(save_name=save_name)
  else:
    raise ValueError(f"Unknown vector database type: {db_type}")
