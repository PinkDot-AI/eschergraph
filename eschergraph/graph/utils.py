from __future__ import annotations

from pathlib import Path

from eschergraph.exceptions import DocumentAlreadyExistsException
from eschergraph.exceptions import FileException
from eschergraph.persistence import Repository


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
