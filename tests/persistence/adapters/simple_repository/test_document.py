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
