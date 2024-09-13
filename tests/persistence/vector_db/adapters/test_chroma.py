from __future__ import annotations

import random
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

import pytest

from eschergraph.agents import Embedding
from eschergraph.persistence.vector_db.adapters import ChromaDB
from eschergraph.persistence.vector_db.vector_search_result import VectorSearchResult
from tests.persistence.vector_db.help import generate_insert_data


@pytest.fixture(scope="function")
def chroma_unit() -> ChromaDB:
  def random_vector(list_text: list[str]) -> list[list[float]]:
    return [[random.random() for _ in range(100)] for _ in range(len(list_text))]

  mock_embedding: MagicMock = MagicMock(spec=Embedding)
  mock_embedding.get_embedding.side_effect = random_vector

  return ChromaDB(
    save_name="unit-test", embedding_model=mock_embedding, persistent=False
  )


def test_chroma_insert_vector(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data()
  test_collection: str = "insert_test"

  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )

  assert set(chroma_unit.client.get_collection(test_collection).peek()["ids"]) == {
    str(id) for id in ids
  }


def test_chroma_delete_by_ids(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data()
  test_collection: str = "delete_test"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  chroma_unit.delete_by_ids(ids=ids, collection_name=test_collection)

  assert not chroma_unit.client.get_collection(test_collection).peek()["ids"]


def test_chroma_search(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data()
  test_collection: str = "search_test"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  results: list[VectorSearchResult] = chroma_unit.search(
    query="test", top_n=5, collection_name=test_collection
  )

  assert {r.id for r in results} < set(ids)


def test_chroma_search_less_in_collection_than_top_n(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data()
  test_collection: str = "search_test_less_than"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  results: list[VectorSearchResult] = chroma_unit.search(
    query="test", top_n=15, collection_name=test_collection
  )

  assert {r.id for r in results} == set(ids)


def test_chroma_search_with_metadata(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data()

  # Change the metadata to allow for filtering on a document
  doc1: UUID = uuid4()
  doc2: UUID = uuid4()

  for i in range(5):
    metadatas[i]["document_id"] = str(doc1)

  for i in range(5, 10):
    metadatas[i]["document_id"] = str(doc2)

  test_collection: str = "search_test"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  results: list[VectorSearchResult] = chroma_unit.search(
    query="test",
    top_n=5,
    collection_name=test_collection,
    metadata={"document_id": str(doc1)},
  )

  assert {r.id for r in results} == set(ids[0:5])


def test_chroma_search_with_metadata_list(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data(num_docs=15)

  # Change the metadata to allow for filtering on a document
  doc1: UUID = uuid4()
  doc2: UUID = uuid4()
  doc3: UUID = uuid4()

  for i in range(5):
    metadatas[i]["document_id"] = str(doc1)

  for i in range(5, 10):
    metadatas[i]["document_id"] = str(doc2)

  for i in range(10, 15):
    metadatas[i]["document_id"] = str(doc3)

  test_collection: str = "search_test"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  results: list[VectorSearchResult] = chroma_unit.search(
    query="test",
    top_n=10,
    collection_name=test_collection,
    metadata={"document_id": [str(doc1), str(doc2)]},
  )

  assert {r.id for r in results} == set(ids[0:10])


def test_chroma_search_with_metadata_list_and_level(chroma_unit: ChromaDB) -> None:
  docs, ids, metadatas = generate_insert_data(num_docs=15)

  # Change the metadata to allow for filtering on a document
  doc1: UUID = uuid4()
  doc2: UUID = uuid4()
  doc3: UUID = uuid4()

  level_14_idxs: list[int] = []

  for i in range(5):
    metadatas[i]["document_id"] = str(doc1)
    # Even and odd are level 14 / 15
    if i % 2 == 0:
      metadatas[i]["level"] = 14
      level_14_idxs.append(i)
    else:
      metadatas[i]["level"] = 15

  for i in range(5, 10):
    metadatas[i]["document_id"] = str(doc2)

  for i in range(10, 15):
    metadatas[i]["document_id"] = str(doc3)
    # Even and odd are level 14 / 15
    if i % 2 == 0:
      metadatas[i]["level"] = 14
      level_14_idxs.append(i)
    else:
      metadatas[i]["level"] = 15

  test_collection: str = "search_test"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  results: list[VectorSearchResult] = chroma_unit.search(
    query="test",
    top_n=10,
    collection_name=test_collection,
    metadata={"document_id": [str(doc1), str(doc3)], "level": 14},
  )

  assert {r.id for r in results} == {[ids[idx] for idx in level_14_idxs]}


def test_chroma_search_with_metadata_single_document_level(
  chroma_unit: ChromaDB,
) -> None:
  docs, ids, metadatas = generate_insert_data()

  # Change the metadata to allow for filtering on a document
  doc1: UUID = uuid4()
  doc2: UUID = uuid4()

  for i in range(5):
    metadatas[i]["document_id"] = str(doc1)

  for i in range(5, 10):
    metadatas[i]["document_id"] = str(doc2)

  # Set the level to 14
  metadatas[0]["level"] = 14
  metadatas[5]["level"] = 14

  test_collection: str = "search_test"
  chroma_unit.insert(
    documents=docs, ids=ids, metadata=metadatas, collection_name=test_collection
  )
  results: list[VectorSearchResult] = chroma_unit.search(
    query="test",
    top_n=10,
    collection_name=test_collection,
    metadata={"document_id": [str(doc1)], "level": 14},
  )

  assert {r.id for r in results} == {ids[0]}
