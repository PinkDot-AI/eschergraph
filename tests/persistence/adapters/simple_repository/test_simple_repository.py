from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Callable
from uuid import UUID

import pytest

from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState
from eschergraph.persistence import Metadata
from eschergraph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.persistence.change_log import Action
from eschergraph.persistence.change_log import ChangeLog
from eschergraph.persistence.document import DocumentData
from eschergraph.persistence.exceptions import DirectoryDoesNotExistException
from eschergraph.persistence.exceptions import FilesMissingException
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge
from tests.graph.help import create_node_only_multi_level_graph
from tests.graph.help import create_property
from tests.graph.help import create_simple_extracted_graph


def test_filenames_function_default() -> None:
  filenames: dict[str, str] = SimpleRepository._filenames(
    save_location=DEFAULT_SAVE_LOCATION, name=DEFAULT_GRAPH_NAME
  )
  base_filename: str = "./eschergraph_storage/escher_default"
  assert filenames == {
    "nodes": base_filename + "-nodes.pkl",
    "edges": base_filename + "-edges.pkl",
    "doc_node_name_index": base_filename + "-nnindex.pkl",
    "properties": base_filename + "-properties.pkl",
    "documents": base_filename + "-documents.pkl",
    "original_build_logs": base_filename + "-ogbuidlogs.pkl",
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
    "doc_node_name_index": base_filename + "-nnindex.pkl",
    "properties": base_filename + "-properties.pkl",
    "documents": base_filename + "-documents.pkl",
    "original_build_logs": base_filename + "-ogbuidlogs.pkl",
  }


def test_new_graph_init_default(tmp_path: Path) -> None:
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  assert repository.nodes == dict()
  assert repository.edges == dict()
  assert repository.doc_node_name_index == dict()
  assert repository.documents == dict()
  assert repository.original_build_logs == dict()


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
  assert node_model["properties"] == [prop.id for prop in node.properties]
  assert node_model["level"] == node.level
  assert {Metadata(**md) for md in node_model["metadata"]} == node.metadata
  assert "child_nodes" in node_model


def test_edge_to_edge_model() -> None:
  edge: Edge = create_edge()
  edge_model: EdgeModel = SimpleRepository._new_edge_to_edge_model(edge)

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
        assert SimpleRepository._select_attributes_to_load(object, loadstate) == []
      else:
        assert_set: set[str] = set()
        for i in range(object_loadstate.value + 1, loadstate.value + 1):
          assert_set = assert_set | attributes_state[i]
        assert (
          set(SimpleRepository._select_attributes_to_load(object, loadstate))
          == assert_set
        )


def test_get_node_by_name(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  node: Node = create_basic_node(repository=repository)
  repository.add(node)

  assert (
    repository.get_node_by_name(
      name=node.name, document_id=next(iter(node.metadata)).document_id
    )
    == node
  )


def test_get_all_at_level(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  _, nodes, _ = create_simple_extracted_graph(repository=repository)

  level_0: list[Node] = repository.get_all_at_level(level=0)
  level_1: list[Node] = repository.get_all_at_level(level=1)

  assert {n.id for n in nodes} == {n.id for n in level_0}
  assert not level_1


def test_get_max_level(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  max_level = 7
  _ = create_node_only_multi_level_graph(max_level=max_level, repository=repository)

  assert repository.get_max_level() == max_level


def test_change_log_initial(saved_graph_dir: Path) -> None:
  assert SimpleRepository(save_location=saved_graph_dir.as_posix()).change_log == []


def setup_change_log_objects(
  repository: SimpleRepository,
) -> tuple[Node, Node, Edge, Property]:
  node1: Node = create_basic_node(repository=repository)
  node2: Node = create_basic_node(repository=repository)
  node1._properties = []
  node2._properties = []
  edge: Edge = create_edge(repository=repository, frm=node1, to=node2)
  property: Property = create_property(node=node1, repository=repository)

  return node1, node2, edge, property


def test_change_log_adding(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  node1, node2, edge, property = setup_change_log_objects(repository)

  assert repository.get_change_log() == []

  repository.add(node1)
  repository.add(node2)
  repository.add(edge)
  repository.add(property)

  change_logs: list[ChangeLog] = repository.get_change_log()
  object_logs: dict[UUID, list[Action]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    object_logs[log.id].append(log.action)

  # Assert that each item was logged as created
  for action_list in object_logs.values():
    assert Action.CREATE in action_list

  assert {log.id for log in change_logs} == {node1.id, node2.id, edge.id, property.id}

  repository.clear_change_log()
  assert repository.get_change_log() == []


def test_change_log_adding_indirectly(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  node1, node2, edge, property = setup_change_log_objects(repository)

  assert repository.get_change_log() == []

  repository.add(node1)

  change_logs: list[ChangeLog] = repository.get_change_log()
  object_logs: dict[UUID, list[Action]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    object_logs[log.id].append(log.action)

  # Assert that each item was logged as created
  for action_list in object_logs.values():
    assert Action.CREATE in action_list

  assert {log.id for log in change_logs} == {node1.id, node2.id, edge.id, property.id}

  repository.clear_change_log()
  assert repository.get_change_log() == []


def test_change_log_updating(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  node1, node2, edge, property = setup_change_log_objects(repository)

  repository.add(node1)
  repository.clear_change_log()
  assert repository.get_change_log() == []

  node1.name = "new name1"
  node2.name = "new name2"
  edge.description = "new edge description"
  property.description = "new property description"

  repository.add(node1)
  repository.add(node2)

  change_logs: list[ChangeLog] = repository.get_change_log()
  objects_actions: dict[UUID, list[Action]] = {log.id: [] for log in change_logs}

  for log in change_logs:
    objects_actions[log.id].append(log.action)

  assert {
    action for log_id in objects_actions.keys() for action in objects_actions[log_id]
  }
  assert set(objects_actions.keys()) == {node1.id, node2.id, edge.id, property.id}


def test_change_log_deleting_indirectly(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  node1, node2, edge, property = setup_change_log_objects(repository)

  repository.add(node1)
  repository.clear_change_log()

  node1.edges = set()
  node1.properties = []
  repository.add(node1)

  change_logs: list[ChangeLog] = repository.get_change_log()
  objects_logs: dict[UUID, list[ChangeLog]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    objects_logs[log.id].append(log)

  assert [log.action for log in objects_logs[edge.id]] == [Action.DELETE]
  assert [log.action for log in objects_logs[property.id]] == [Action.DELETE]
  assert [log.action for log in objects_logs[node1.id]] == [Action.UPDATE]
  assert [log.action for log in objects_logs[node2.id]] == [Action.UPDATE]


def test_change_log_deleting_document(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  _, nodes, edges = create_simple_extracted_graph(repository=repository)
  property_ids: list[UUID] = [prop.id for node in nodes for prop in node.properties]

  assert repository.get_change_log()
  repository.clear_change_log()

  # Add and create the document object
  metadata: Metadata = next(iter(nodes[0].metadata))
  document: DocumentData = DocumentData(
    id=metadata.document_id, name="test.pdf", chunk_num=100, token_num=100
  )
  repository.add_document(document)

  repository.remove_document_by_id(document.id)
  change_logs: list[ChangeLog] = repository.get_change_log()
  objects_logs: dict[UUID, list[ChangeLog]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    objects_logs[log.id].append(log)

  for object_id in chain([n.id for n in nodes], [e.id for e in edges], property_ids):
    assert Action.DELETE in {log.action for log in objects_logs[object_id]}
