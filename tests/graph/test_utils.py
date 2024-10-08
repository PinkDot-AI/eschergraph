from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from unittest.mock import Mock
from uuid import uuid4

import pytest

from eschergraph.exceptions import DocumentAlreadyExistsException
from eschergraph.exceptions import DocumentDoesNotExistException
from eschergraph.exceptions import FileException
from eschergraph.graph.utils import duplicate_document_check
from eschergraph.graph.utils import get_document_ids_from_filenames
from eschergraph.graph.utils import search_check
from eschergraph.persistence.document import Document
from tests.graph.help import create_basic_node


# Temporarily change the working directory to setup test files
@contextmanager
def change_dir(destination: str) -> Generator[None, None, None]:
  original_dir: str = os.getcwd()
  try:
    os.chdir(destination)
    yield
  finally:
    os.chdir(original_dir)


def test_duplicate_document_check_empty(mock_repository: Mock) -> None:
  duplicate_document_check(file_list=[], repository=mock_repository)


def test_duplicate_document_check_no_duplicates(
  saved_graph_dir: Path, mock_repository: Mock
) -> None:
  mock_repository.get_document_by_name.return_value = None

  # Setup to make sure the provided filepaths do actually exist
  with change_dir(saved_graph_dir.as_posix()):
    test_file: Path = saved_graph_dir / "test_file.pdf"
    test_docx_dir: Path = saved_graph_dir / "docs" / "folder"
    test_docx: Path = test_docx_dir / "test_doc.xlsx"
    test_dir: Path = saved_graph_dir / "hello"
    test: Path = test_dir / "test.docx"

    test_docx_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    test_file.touch()
    test_docx.touch()
    test.touch()

    files: list[str] = [
      "test_file.pdf",
      "./docs/folder/test_doc.xlsx",
      "./hello/test.docx",
    ]
    duplicate_document_check(file_list=files, repository=mock_repository)

  call_args: list[str] = [
    call[0][0] for call in mock_repository.get_document_by_name.call_args_list
  ]

  assert len(call_args) == 3
  assert call_args == ["test_file.pdf", "test_doc.xlsx", "test.docx"]


def test_duplicate_document_check_file_does_not_exist(
  saved_graph_dir: Path, mock_repository: Mock
) -> None:
  mock_repository.get_document_by_name.return_value = None
  files: list[str] = ["./docs/folder/test.pdf"]

  # Setup to make sure the provided directory does exist
  with change_dir(saved_graph_dir.as_posix()):
    test_dir: Path = saved_graph_dir / "docs" / "folder"
    test_dir.mkdir(parents=True)

    with pytest.raises(FileException):
      duplicate_document_check(file_list=files, repository=mock_repository)


def test_duplicate_document_check_file_is_not_a_file(
  saved_graph_dir: Path, mock_repository: Mock
) -> None:
  mock_repository.get_document_by_name.return_value = None
  files: list[str] = ["./docs/folder"]

  # Setup to make sure the provided directory does exist
  with change_dir(saved_graph_dir.as_posix()):
    os.chdir(saved_graph_dir.as_posix())
    test_dir: Path = saved_graph_dir / "docs" / "folder"
    test_dir.mkdir(parents=True)

    with pytest.raises(FileException):
      duplicate_document_check(file_list=files, repository=mock_repository)


def test_duplicate_document_check_file_already_exists(
  saved_graph_dir: Path, mock_repository: Mock
) -> None:
  mock_repository.get_document_by_name.side_effect = [
    None,
    Document(id=uuid4(), name="test_doc.xlsx", chunk_num=1, token_num=100),
  ]

  # Setup to make sure the provided filepaths do actually exist
  with change_dir(saved_graph_dir.as_posix()):
    test_file: Path = saved_graph_dir / "test_file.pdf"
    test_docx_dir: Path = saved_graph_dir / "docs" / "folder"
    test_docx: Path = test_docx_dir / "test_doc.xlsx"

    test_docx_dir.mkdir(parents=True)
    test_file.touch()
    test_docx.touch()

    files: list[str] = [test_file.as_posix(), test_docx.as_posix()]

    with pytest.raises(DocumentAlreadyExistsException):
      duplicate_document_check(file_list=files, repository=mock_repository)

    call_args: list[str] = [
      call[0][0] for call in mock_repository.get_document_by_name.call_args_list
    ]

    assert len(call_args) == 2
    assert call_args == ["test_file.pdf", "test_doc.xlsx"]


def test_search_check_empty_graph(mock_repository: Mock) -> None:
  mock_repository.get_all_at_level.return_value = []

  assert not search_check(mock_repository)
  mock_repository.get_all_at_level.assert_called_once()


def test_search_check_nodes_at_level_0(mock_repository: Mock) -> None:
  mock_repository.get_all_at_level.return_value = [
    create_basic_node(mock_repository),
    create_basic_node(mock_repository),
  ]

  assert search_check(mock_repository)
  mock_repository.get_all_at_level.assert_called_once()


def test_get_document_ids_from_filenames_empty(mock_repository: Mock) -> None:
  assert not get_document_ids_from_filenames([], mock_repository)


def test_get_document_ids_from_filenames(mock_repository: Mock) -> None:
  doc1: Document = Document(id=uuid4(), name="doc1.pdf", chunk_num=100, token_num=100)
  doc2: Document = Document(id=uuid4(), name="doc2.xlsx", chunk_num=100, token_num=100)
  mock_repository.get_document_by_name.side_effect = [doc1, doc2]

  assert [doc1.id, doc2.id] == get_document_ids_from_filenames(
    ["doc1.pdf", "doc2.xlsx"], mock_repository
  )


def test_get_document_ids_from_filenames_doc_not_found(mock_repository: Mock) -> None:
  doc1: Document = Document(id=uuid4(), name="doc1.pdf", chunk_num=100, token_num=100)
  doc2: Document = Document(id=uuid4(), name="doc2.xlsx", chunk_num=100, token_num=100)
  mock_repository.get_document_by_name.side_effect = [doc1, None]

  with pytest.raises(DocumentDoesNotExistException):
    get_document_ids_from_filenames(["doc1.pdf", "doc2.xlsx"], mock_repository)
