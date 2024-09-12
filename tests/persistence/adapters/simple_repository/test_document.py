from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from eschergraph.exceptions import DocumentDoesNotExistException
from eschergraph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.persistence.document import DocumentData


def test_document_add(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  repository.add_document(document)
  repository.save()

  del repository

  new_repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  assert new_repository.documents == {document.id: document}
  assert new_repository.get_documents_by_id([document.id]) == [document]


def test_document_get(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  document2: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )

  repository.add_document(document1)
  repository.add_document(document2)

  assert repository.documents == {
    document.id: document for document in [document1, document2]
  }
  assert repository.get_documents_by_id([document1.id, document2.id]) == [
    document1,
    document2,
  ]
  assert set(repository.doc_node_name_index.keys()) == {document1.id, document2.id}


def test_document_change(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  document2: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )

  repository.add_document(document1)
  repository.add_document(document2)
  document1.name = "new_name.pdf"
  repository.add_document(document1)

  assert repository.documents == {
    document.id: document for document in [document1, document2]
  }
  assert repository.get_documents_by_id([document1.id, document2.id]) == [
    document1,
    document2,
  ]


def test_document_remove(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  document1: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )
  document2: DocumentData = DocumentData(
    id=uuid4(), name="test document", chunk_num=100, token_num=1000
  )

  repository.add_document(document1)
  repository.add_document(document2)
  repository.remove_document_by_id(document1.id)

  assert repository.documents == {document.id: document for document in [document2]}
  assert repository.get_documents_by_id([document1.id, document2.id]) == [document2]


def test_document_remove_does_not_exist(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  with pytest.raises(DocumentDoesNotExistException):
    repository.remove_document_by_id(uuid4())
