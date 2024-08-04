from __future__ import annotations

from pathlib import Path

import pytest

from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.exceptions import DirectoryDoesNotExistException
from eschergraph.graph.persistence.exceptions import FilesMissingException


def test_filenames_function_default() -> None:
  filenames: dict[str, str] = SimpleRepository._filenames(
    save_location=DEFAULT_SAVE_LOCATION, name=DEFAULT_GRAPH_NAME
  )
  base_filename: str = "./eschergraph-storage/escher_default"
  assert filenames == {
    "nodes": base_filename + "-nodes.pkl",
    "edges": base_filename + "-edges.pkl",
    "node_name_index": base_filename + "-nnindex.pkl",
  }


def test_filenames_function_specified() -> None:
  save_location: str = "C:/pinkdot/eschergraphs"
  name: str = "global"
  filenames: dict[str, str] = SimpleRepository._filenames(
    save_location=save_location, name=name
  )
  base_filename: str = save_location + "/" + name
  assert filenames == {
    "nodes": base_filename + "-nodes.pkl",
    "edges": base_filename + "-edges.pkl",
    "node_name_index": base_filename + "-nnindex.pkl",
  }


def test_new_graph_init_default(tmp_path: Path) -> None:
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  assert repository.nodes == dict()
  assert repository.edges == dict()
  assert repository.node_name_index == dict()


def test_init_dir_does_not_exist() -> None:
  with pytest.raises(DirectoryDoesNotExistException):
    SimpleRepository(save_location="TMP/does-not-exist12345")


@pytest.mark.parametrize("file_indexes", [(0, 1), (1, 2), (0, 2), (0,), (1,), (2,)])
def test_init_files_corrupted(saved_graph_dir: Path, file_indexes: tuple[int]) -> None:
  files: list[str] = ["default-nodes.pkl", "default-edges.pkl", "default-nnindex.pkl"]
  for idx in file_indexes:
    file: Path = saved_graph_dir / files[idx]
    file.touch()

  with pytest.raises(FilesMissingException):
    SimpleRepository(name="default", save_location=saved_graph_dir.as_posix())
