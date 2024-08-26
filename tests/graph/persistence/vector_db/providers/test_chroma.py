from __future__ import annotations

from unittest.mock import call
from unittest.mock import Mock

import pytest

from eschergraph.graph.persistence.vector_db.adapters.chromadb import ChromaDB


@pytest.fixture
def vector_db_mock() -> Mock:
  """
  Fixture that returns a mocked instance of the ChromaDB class.
  """
  vector_db_mock = Mock(spec=ChromaDB)

  # Mock the embedding model and its get_embedding method
  vector_db_mock.embedding_model = Mock()

  return vector_db_mock


def test_insert_documents(vector_db_mock: Mock) -> None:
  """
  Test the insert_documents method.
  """
  collection_name = "test_collection"
  vector_db_mock.create_collection(collection_name)

  docs = ["hello", "tests", "correct"]
  ids = [str(i) for i in range(len(docs))]
  metadata = [
    {"document": "hello.pdf", "graph_type": "Node", "parent_node": ""},
    {"document": "test.pdf", "graph_type": "Edge", "parent_node": ""},
    {"document": "test.pdf", "graph_type": "Edge", "parent_node": ""},
  ]

  vector_db_mock.embedding_model.get_embedding.return_value = [
    [1.0, 2.0, 3.0],
    [1.0, 2.0, 4.0],
    [1.0, 3.0, 4.0],
  ]

  vector_db_mock.insert_documents(
    documents=docs,
    ids=ids,
    metadata=metadata,
    collection_name=collection_name,
  )

  vector_db_mock.insert_documents.assert_called_once_with(
    documents=docs,
    ids=ids,
    metadata=metadata,
    collection_name=collection_name,
  )


def test_search_edge_type(vector_db_mock: Mock) -> None:
  """
  Test the search method for Edge type.
  """
  collection_name = "test_collection"
  vector_db_mock.embedding_model.get_embedding.return_value = [[1.2, 2.1, 3.1]]
  vector_db_mock.search.return_value = {"result_1": "some_result_1"}

  results_1: dict[str, str] = vector_db_mock.search(
    query="mock",
    top_n=2,
    metadata={"graph_type": "Edge"},
    collection_name=collection_name,
  )

  vector_db_mock.search.assert_called_with(
    query="mock",
    top_n=2,
    metadata={"graph_type": "Edge"},
    collection_name=collection_name,
  )
  assert results_1 == {"result_1": "some_result_1"}


def test_search_node_type(vector_db_mock: Mock) -> None:
  """
  Test the search method for Node type.
  """
  collection_name = "test_collection"
  vector_db_mock.embedding_model.get_embedding.return_value = [[1.2, 2.1, 3.4]]
  vector_db_mock.search.return_value = {"result_2": "some_result_2"}

  results_2: dict[str, str] = vector_db_mock.search(
    query="mock",
    top_n=2,
    metadata={"graph_type": "Node"},
    collection_name=collection_name,
  )

  vector_db_mock.search.assert_called_with(
    query="mock",
    top_n=2,
    metadata={"graph_type": "Node"},
    collection_name=collection_name,
  )
  assert results_2 == {"result_2": "some_result_2"}


def test_delete_with_id(vector_db_mock: Mock) -> None:
  """
  Test the delete_with_id method.
  """
  collection_name = "test_collection"

  vector_db_mock.delete_with_id(collection_name=collection_name, ids=["2"])

  vector_db_mock.delete_with_id.assert_called_once_with(
    collection_name=collection_name, ids=["2"]
  )


def test_delete_with_metadata(vector_db_mock: Mock) -> None:
  """
  Test the delete_with_metadata method.
  """
  collection_name = "test_collection"

  vector_db_mock.delete_with_metadata(
    collection_name=collection_name, metadata={"graph_type": "Node"}
  )

  vector_db_mock.delete_with_metadata.assert_called_once_with(
    collection_name=collection_name, metadata={"graph_type": "Node"}
  )


def test_method_call_sequence(vector_db_mock: Mock) -> None:
  """
  Test the sequence of method calls.
  """
  collection_name = "test_collection"

  docs = ["hello", "tests", "correct"]
  ids = [str(i) for i in range(len(docs))]
  metadata = [
    {"document": "hello.pdf", "graph_type": "Node", "parent_node": ""},
    {"document": "test.pdf", "graph_type": "Edge", "parent_node": ""},
    {"document": "test.pdf", "graph_type": "Edge", "parent_node": ""},
  ]

  vector_db_mock.embedding_model.get_embedding.return_value = [
    [1.0, 2.0, 3.0],
    [1.0, 2.0, 4.0],
    [1.0, 3.0, 4.0],
  ]

  vector_db_mock.create_collection(collection_name)
  vector_db_mock.insert_documents(
    documents=docs,
    ids=ids,
    metadata=metadata,
    collection_name=collection_name,
  )
  vector_db_mock.search(
    query="mock",
    top_n=2,
    metadata={"graph_type": "Edge"},
    collection_name=collection_name,
  )
  vector_db_mock.search(
    query="mock",
    top_n=2,
    metadata={"graph_type": "Node"},
    collection_name=collection_name,
  )
  vector_db_mock.delete_with_id(collection_name=collection_name, ids=["2"])
  vector_db_mock.delete_with_metadata(
    collection_name=collection_name, metadata={"graph_type": "Node"}
  )

  vector_db_mock.assert_has_calls([
    call.create_collection(collection_name),
    call.insert_documents(
      documents=docs,
      ids=ids,
      metadata=metadata,
      collection_name=collection_name,
    ),
    call.search(
      query="mock",
      top_n=2,
      metadata={"graph_type": "Edge"},
      collection_name=collection_name,
    ),
    call.search(
      query="mock",
      top_n=2,
      metadata={"graph_type": "Node"},
      collection_name=collection_name,
    ),
    call.delete_with_id(collection_name=collection_name, ids=["2"]),
    call.delete_with_metadata(
      collection_name=collection_name, metadata={"graph_type": "Node"}
    ),
  ])
