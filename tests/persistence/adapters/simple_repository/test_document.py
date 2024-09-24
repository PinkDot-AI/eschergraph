from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from eschergraph.exceptions import DocumentDoesNotExistException
from eschergraph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.persistence.document import Document


def test_document_add(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  repository.add_document(document)
  repository.save()

  del repository

  new_repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  assert new_repository.documents == {document.id: document}
  assert new_repository.get_document_by_id(document.id) == document


def test_document_get(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  document2: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )

  repository.add_document(document1)
  repository.add_document(document2)

  assert repository.documents == {
    document.id: document for document in [document1, document2]
  }
  assert repository.get_document_by_id(document1.id) == document1
  assert repository.get_document_by_id(document2.id) == document2
  assert set(repository.doc_node_name_index.keys()) == {document1.id, document2.id}


def test_document_change(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  document2: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )

  repository.add_document(document1)
  repository.add_document(document2)
  document1.name = "new_name.pdf"
  repository.add_document(document1)

  assert repository.documents == {
    document.id: document for document in [document1, document2]
  }
  assert repository.get_document_by_id(document1.id) == document1
  assert repository.get_document_by_id(document2.id) == document2


def test_get_all_documents(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: Document = Document(id=uuid4(), name="doc1", chunk_num=100, token_num=1000)
  document2: Document = Document(id=uuid4(), name="doc2", chunk_num=100, token_num=1000)
  document3: Document = Document(id=uuid4(), name="doc3", chunk_num=100, token_num=1000)

  repository.add_document(document1)
  repository.add_document(document2)
  repository.add_document(document3)

  assert {doc.id for doc in repository.get_all_documents()} == {
    doc.id for doc in [document1, document2, document3]
  }


def get_document_by_name(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  doc: Document = Document(id=uuid4(), name="doc.pdf", chunk_num=100, token_num=1000)

  repository.add_document(doc)

  assert repository.get_document_by_name("doc.pdf") == doc


def get_document_by_name_no_match(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  doc: Document = Document(id=uuid4(), name="doc.pdf", chunk_num=100, token_num=1000)

  repository.add_document(doc)

  assert not repository.get_document_by_name("doc1.pdf")


def test_document_remove(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  document2: Document = Document(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )

  repository.add_document(document1)
  repository.add_document(document2)
  repository.remove_document_by_id(document1.id)

  assert repository.documents == {document.id: document for document in [document2]}
  assert not repository.get_document_by_id(document1.id)
  assert repository.get_document_by_id(document2.id) == document2


def test_document_remove_does_not_exist(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  with pytest.raises(DocumentDoesNotExistException):
    repository.remove_document_by_id(uuid4())


def test_list_available_tags_empty(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  assert repository.list_available_tags() == {}


def test_list_available_tags_two_documents(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)

  assert repository.list_available_tags() == {
    "type": "str",
    "field": "int",
    "is_latest": "bool",
  }


def test_add_documents_tags(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)

  assert repository.doc_tags == {
    "type": ("str", 2),
    "field": ("int", 1),
    "is_latest": ("bool", 1),
  }


def test_delete_documents_tags(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)

  assert repository.list_available_tags() == {
    "type": "str",
    "field": "int",
    "is_latest": "bool",
  }
  assert repository.doc_tags == {
    "type": ("str", 2),
    "field": ("int", 1),
    "is_latest": ("bool", 1),
  }

  repository.remove_document_by_id(id=doc1.id)

  assert repository.list_available_tags() == {"type": "str", "is_latest": "bool"}
  assert repository.doc_tags == {"type": ("str", 1), "is_latest": ("bool", 1)}

  repository.remove_document_by_id(id=doc2.id)

  assert repository.list_available_tags() == {}
  assert repository.doc_tags == {}


def test_add_document_twice_unchanged_tags(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )

  repository.add_document(doc1)
  repository.add_document(doc1)

  assert repository.list_available_tags() == {"type": "str", "field": "int"}
  assert repository.doc_tags == {"type": ("str", 1), "field": ("int", 1)}


def test_add_document_twice_changed_tags(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  repository.add_document(doc1)

  doc1.tags = {"type": "magazine", "status": "published"}
  repository.add_document(doc1)

  assert repository.list_available_tags() == {"type": "str", "status": "str"}
  assert repository.doc_tags == {"type": ("str", 1), "status": ("str", 1)}


def test_add_documents_remove_tags(
  saved_graph_dir: Path,
) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )
  doc3: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "is_latest": True},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)
  repository.add_document(doc3)

  assert repository.doc_tags == {
    "type": ("str", 3),
    "is_latest": ("bool", 2),
    "field": ("int", 1),
  }

  doc3.tags = {"is_latest": True, "size": 24}
  repository.add_document(doc3)

  assert repository.doc_tags == {
    "type": ("str", 2),
    "is_latest": ("bool", 2),
    "field": ("int", 1),
    "size": ("int", 1),
  }


def test_filter_documents_no_result(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)

  assert repository.filter_documents_by_tags(filter_tags={"type": "magazine"}) == []


def test_filter_documents_single_result(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)

  assert repository.filter_documents_by_tags(filter_tags={"field": 23}) == [doc1]


def test_filter_documents_ignore_missing_tags(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)

  assert set(
    repository.filter_documents_by_tags(
      filter_tags={"field": 23}, ignore_missing_tags=True
    )
  ) == {doc1, doc2}


def test_filter_documents_multiple_filter_tags_ignore_missing(
  saved_graph_dir: Path,
) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  doc1: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "field": 23},
  )
  doc2: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "paper", "is_latest": False},
  )
  doc3: Document = Document(
    id=uuid4(),
    name="test document",
    chunk_num=100,
    token_num=1000,
    tags={"type": "report", "is_latest": True},
  )

  repository.add_document(doc1)
  repository.add_document(doc2)
  repository.add_document(doc3)

  assert set(
    repository.filter_documents_by_tags(
      filter_tags={"type": "report", "field": 23, "is_latest": True},
      ignore_missing_tags=True,
    )
  ) == {doc1, doc3}
