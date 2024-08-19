from __future__ import annotations

from pathlib import Path

import pytest

from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.graph.persistence.exceptions import DirectoryDoesNotExistException
from eschergraph.graph.persistence.exceptions import FilesMissingException
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge


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


def test_node_to_node_model() -> None:
  node: Node = create_basic_node()
  node_model: NodeModel = SimpleRepository._new_node_to_node_model(node)

  assert node_model["name"] == node.name
  assert node_model["description"] == node.description
  assert node_model["properties"] == node.properties
  assert node_model["level"] == node.level
  assert {Metadata(**md) for md in node_model["metadata"]} == node.metadata


def test_attributes_to_add_node() -> None:
  node_reference: Node = create_basic_node()
  node_reference._loadstate = LoadState.REFERENCE

  node_core: Node = create_basic_node()
  node_core._loadstate = LoadState.CORE
  core_attributes: set[str] = {"name", "description", "level", "properties", "metadata"}

  node_connected: Node = create_basic_node()
  node_connected._loadstate = LoadState.CONNECTED
  connected_attributes: set[str] = core_attributes | {"edges"}

  node_full: Node = create_basic_node()
  node_full._loadstate = LoadState.FULL
  full_attributes: set[str] = connected_attributes | {
    "community",
    "child_nodes",
    "report",
  }

  assert SimpleRepository._select_attributes_to_add(node_reference) == []
  assert set(SimpleRepository._select_attributes_to_add(node_core)) == core_attributes
  assert (
    set(SimpleRepository._select_attributes_to_add(node_connected))
    == connected_attributes
  )
  assert set(SimpleRepository._select_attributes_to_add(node_full)) == full_attributes


def test_attributes_to_add_edge() -> None:
  edge_reference: Edge = create_edge()
  edge_reference._loadstate = LoadState.REFERENCE

  edge_core: Edge = create_edge()
  edge_core._loadstate = LoadState.CORE
  core_attributes: set[str] = {"metadata", "description"}

  edge_full: Edge = create_edge()
  edge_full._loadstate = LoadState.FULL

  assert SimpleRepository._select_attributes_to_add(edge_reference) == []
  assert set(SimpleRepository._select_attributes_to_add(edge_core)) == core_attributes
  assert set(SimpleRepository._select_attributes_to_add(edge_full)) == core_attributes


def test_attributes_to_load_node() -> None: ...


def test_attributes_to_load_edge() -> None: ...
