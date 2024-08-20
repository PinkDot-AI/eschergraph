from __future__ import annotations

from eschergraph.graph.persistence.vector_db.vector_db import VectorDB
from eschergraph.graph.persistence.vector_db.vector_db_factory import get_vector_db


def test_chroma() -> None:
  """
  Testing the searching and inserting of the chroma db vector database implementation
  """
  vector_db: VectorDB = get_vector_db("chroma_db")
  collection_name: str = "test_collection"
  vector_db.create_collection(collection_name)
  docs: list[str] = ["hello", "tests", "correct"]
  embeddings: list[list[float]] = [[1, 2, 3], [2, 0.5, -1], [1, 2, 4]]
  ids = [str(i) for i in range(len(docs))]
  metadata: list[dict[str, str]] = [
    {
      "document": "hello.pdf",
      "graph_type": "Node",
      "parent_node": "",
    },
    {
      "document": "test.pdf",
      "graph_type": "Edge",
      "parent_node": "",
    },
    {
      "document": "test.pdf",
      "graph_type": "Edge",
      "parent_node": "",
    },
  ]
<<<<<<< HEAD:tests/graph/persistence/vector_db/adapters/test_chroma.py
  vector_db.insert(
=======
  vector_db.insert_documents(
>>>>>>> main:tests/graph/persistence/vector_db/providers/test_chroma.py
    documents=docs,
    embeddings=embeddings,
    ids=ids,
    metadata=metadata,
    collection_name=collection_name,
  )

  results_1: dict[str, str] = vector_db.search(
    embedding=[1, 2, 4],
    top_n=4,
    metadata={"graph_type": "Edge"},
    collection_name=collection_name,
  )
  results_2: dict[str, str] = vector_db.search(
    embedding=[1, 2, 4],
    top_n=4,
    metadata={"graph_type": "Node"},
    collection_name=collection_name,
  )

  assert results_1["documents"][0][0] == "correct"
  assert results_2["documents"][0][0] == "hello"