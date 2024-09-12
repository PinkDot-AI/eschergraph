from __future__ import annotations

from pathlib import Path

from eschergraph.exceptions import DocumentAlreadyExistsException
from eschergraph.persistence import Repository


def duplicate_document_check(file_list: list[str], repository: Repository) -> None:
  """Check if the documents already exist in the graph.

  Args:
    file_list (list[str]): A list of filepaths pointing to files.
    repository (Repository): The repository that stores the graph data.

  Raises:
    A DocumentAlreadyExistsException as soon as it discovers a document that already
    exists.
  """
  for file in file_list:
    filename: str = Path(file).name
    if repository.get_document_by_name(filename):
      raise DocumentAlreadyExistsException(
        f"A file with this name already exists in the graph: {filename}"
      )
