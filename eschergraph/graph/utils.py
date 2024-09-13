from __future__ import annotations

from pathlib import Path
from uuid import UUID

from eschergraph.exceptions import DocumentAlreadyExistsException
from eschergraph.exceptions import DocumentDoesNotExistException
from eschergraph.exceptions import FileException
from eschergraph.persistence import Repository
from eschergraph.persistence.document import Document


def duplicate_document_check(file_list: list[str], repository: Repository) -> None:
  """Check if the documents already exist in the graph.

  Also, it raises an exception if a provided filepath does not point to
  a file.

  Args:
    file_list (list[str]): A list of filepaths pointing to files.
    repository (Repository): The repository that stores the graph data.

  Raises:
    A DocumentAlreadyExistsException as soon as it discovers a document that already
    exists.
    FileException if one of the provided paths does not point to a file, or if the
    file does not exist.
  """
  for file in file_list:
    file_path: Path = Path(file)

    # Check if the filepath points to a file
    if not file_path.is_file():
      raise FileException(f"Make sure that this is a file that exists: {file_path}")

    filename: str = file_path.name

    if repository.get_document_by_name(filename):
      raise DocumentAlreadyExistsException(
        f"A file with this name already exists in the graph: {filename}"
      )


def search_check(repository: Repository) -> bool:
  """Check if there are any elements at level 0 in the graph repository.

  Args:
    repository (Repository): The repository that stores the graph.

  Returns:
    bool: True if there are elements at level 0, otherwise False.
  """
  return len(repository.get_all_at_level(0)) > 0


def get_document_ids_from_filenames(
  filenames: list[str], repository: Repository
) -> list[UUID]:
  """Get a document id from a list of filenames.

  Used to get the document id's for the filter in the search.

  Args:
    filenames (list[str]): A list of filenames.
    repository (Repository): The repository that saves the data.

  Returns:
    list[UUID]: A list of document id's.

  Raises:
    DocumentDoesNotExistException: If one of the provided filenames does not exist.
  """
  doc_ids: list[UUID] = []
  for name in filenames:
    doc: Document | None = repository.get_document_by_name(name)

    if not doc:
      raise DocumentDoesNotExistException(f"Document with name: {name}, does not exist")
    doc_ids.append(doc.id)

  return doc_ids
