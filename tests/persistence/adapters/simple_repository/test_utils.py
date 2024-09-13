from __future__ import annotations

from typing import Callable

from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState
from eschergraph.persistence import Metadata
from eschergraph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.persistence.adapters.simple_repository.utils import (
  new_edge_to_edge_model,
)
from eschergraph.persistence.adapters.simple_repository.utils import (
  new_node_to_node_model,
)
from eschergraph.persistence.adapters.simple_repository.utils import save_filenames
from eschergraph.persistence.adapters.simple_repository.utils import (
  select_attributes_to_add,
)
from eschergraph.persistence.adapters.simple_repository.utils import (
  select_attributes_to_load,
)
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge


def test_filenames_function_default() -> None:
  filenames: dict[str, str] = save_filenames(
    save_location=DEFAULT_SAVE_LOCATION, name=DEFAULT_GRAPH_NAME
  )
  base_filename: str = "./eschergraph_storage/escher_default"
  assert filenames == {
    "nodes": base_filename + "-nodes.pkl",
    "edges": base_filename + "-edges.pkl",
    "doc_node_name_index": base_filename + "-nnindex.pkl",
    "properties": base_filename + "-properties.pkl",
    "documents": base_filename + "-documents.pkl",
  }


def test_filenames_function_specified() -> None:
  save_location: str = "C:/pinkdot/eschergraphs"
  name: str = "global"
  filenames: dict[str, str] = save_filenames(save_location=save_location, name=name)
  base_filename: str = save_location + "/" + name
  assert filenames == {
    "nodes": base_filename + "-nodes.pkl",
    "edges": base_filename + "-edges.pkl",
    "doc_node_name_index": base_filename + "-nnindex.pkl",
    "properties": base_filename + "-properties.pkl",
    "documents": base_filename + "-documents.pkl",
  }


def test_node_to_node_model() -> None:
  node: Node = create_basic_node()
  node_model: NodeModel = new_node_to_node_model(node)

  assert node_model["name"] == node.name
  assert node_model["description"] == node.description
  assert node_model["properties"] == [prop.id for prop in node.properties]
  assert node_model["level"] == node.level
  assert {Metadata(**md) for md in node_model["metadata"]} == node.metadata
  assert "child_nodes" in node_model


def test_edge_to_edge_model() -> None:
  edge: Edge = create_edge()
  edge_model: EdgeModel = new_edge_to_edge_model(edge)

  assert edge_model["description"] == edge.description
  assert edge_model["frm"] == edge.frm.id
  assert edge_model["to"] == edge.to.id
  assert {Metadata(**md) for md in edge_model["metadata"]} == edge.metadata


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
  full_attributes: set[str] = connected_attributes | {"community", "child_nodes"}

  assert select_attributes_to_add(node_reference) == []
  assert set(select_attributes_to_add(node_core)) == core_attributes
  assert set(select_attributes_to_add(node_connected)) == connected_attributes
  assert set(select_attributes_to_add(node_full)) == full_attributes


def test_attributes_to_add_edge() -> None:
  edge_reference: Edge = create_edge()
  edge_reference._loadstate = LoadState.REFERENCE

  edge_core: Edge = create_edge()
  edge_core._loadstate = LoadState.CORE
  core_attributes: set[str] = {"metadata", "description"}

  edge_full: Edge = create_edge()
  edge_full._loadstate = LoadState.FULL

  assert select_attributes_to_add(edge_reference) == []
  assert set(select_attributes_to_add(edge_core)) == core_attributes
  assert set(select_attributes_to_add(edge_full)) == core_attributes


def test_attributes_to_load_node() -> None:
  attributes_state: dict[int, set[str]] = {
    0: set(),
    1: {"name", "description", "level", "properties", "metadata"},
    2: {"edges"},
    3: {"community", "child_nodes"},
  }
  all_load_combinations(create_basic_node, attributes_state)


def test_attributes_to_load_edge() -> None:
  attributes_state: dict[int, set[str]] = {
    0: set(),
    1: {"description", "metadata"},
    2: set(),
    3: set(),
  }
  all_load_combinations(create_edge, attributes_state)


def all_load_combinations(
  create_function: Callable[[], EscherBase], attributes_state: dict[int, set[str]]
) -> None:
  for object_loadstate in LoadState:
    object: EscherBase = create_function()
    object._loadstate = object_loadstate
    for loadstate in LoadState:
      if object_loadstate.value >= loadstate.value:
        assert select_attributes_to_load(object, loadstate) == []
      else:
        assert_set: set[str] = set()
        for i in range(object_loadstate.value + 1, loadstate.value + 1):
          assert_set = assert_set | attributes_state[i]
        assert set(select_attributes_to_load(object, loadstate)) == assert_set
