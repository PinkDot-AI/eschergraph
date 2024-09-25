from __future__ import annotations

from unittest.mock import Mock
from uuid import UUID
from uuid import uuid4

import pytest

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.persistence.change_log import Action
from eschergraph.persistence.change_log import ChangeLog
from eschergraph.tools.prepare_sync_data import _get_actions_for_objects
from eschergraph.tools.prepare_sync_data import _get_node_document_id
from eschergraph.tools.prepare_sync_data import prepare_sync_data
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge
from tests.graph.help import create_property


def test_prep_sync_vector_db(mock_repository: Mock) -> None:
  # Mock the repository
  node1 = create_basic_node(repository=mock_repository)
  node2 = create_basic_node(repository=mock_repository)
  edge1 = create_edge(repository=mock_repository)
  edge2 = create_edge(repository=mock_repository)
  prop1 = create_property(repository=mock_repository)
  prop2 = create_property(repository=mock_repository)

  # Set up the return values for the mock repo
  mock_repository.get_node_by_id.side_effect = [node1, node2]
  mock_repository.get_edge_by_id.side_effect = [edge1]
  mock_repository.get_property_by_id.side_effect = [prop1]

  change_logs: list[ChangeLog] = [
    ChangeLog(id=node1.id, action=Action.UPDATE, type=Node, level=0),
    ChangeLog(id=node2.id, action=Action.UPDATE, type=Node, level=0),
    ChangeLog(id=edge1.id, action=Action.CREATE, type=Edge, level=0),
    ChangeLog(id=edge2.id, action=Action.DELETE, type=Edge, level=0),
    ChangeLog(id=edge2.id, action=Action.CREATE, type=Edge, level=0),
    ChangeLog(id=node1.id, action=Action.CREATE, type=Node, level=0),
    ChangeLog(id=prop1.id, action=Action.UPDATE, type=Property, level=0),
    ChangeLog(id=prop2.id, action=Action.CREATE, type=Property, level=0),
    ChangeLog(id=prop2.id, action=Action.DELETE, type=Property, level=0),
  ]
  mock_repository.get_change_log.return_value = change_logs

  # Inject the mock repository into the function
  create_main, ids_to_delete = prepare_sync_data(mock_repository)

  ids_to_create, docs_to_create, metadata_to_create = zip(*create_main)

  assert set(ids_to_create) == {node1.id, node2.id, edge1.id, prop1.id}
  assert set(ids_to_delete) == {node2.id, prop1.id}
  assert set(docs_to_create) == {
    node1.name + ", " + node1.description,
    node2.name + ", " + node2.description,
    edge1.description,
    prop1.node.name + ", " + prop1.description,
  }


def test_prep_sync_vector_db_create_correct_level(mock_repository: Mock) -> None:
  node: Node = create_basic_node(repository=mock_repository)
  edge: Edge = create_edge(repository=mock_repository)
  prop: Property = create_property(repository=mock_repository)

  # Set up the return values for the mock repo
  mock_repository.get_node_by_id.side_effect = [node]
  mock_repository.get_edge_by_id.side_effect = [edge]
  mock_repository.get_property_by_id.side_effect = [prop]

  change_logs: list[ChangeLog] = [
    ChangeLog(id=node.id, action=Action.CREATE, type=Node, level=0),
    ChangeLog(id=edge.id, action=Action.CREATE, type=Edge, level=1),
    ChangeLog(id=prop.id, action=Action.DELETE, type=Property, level=12),
  ]
  mock_repository.get_change_log.return_value = change_logs

  # Inject the mock repository into the function
  create_main, _ = prepare_sync_data(mock_repository)
  _, _, metadata_to_create = zip(*create_main)

  for md in metadata_to_create:
    if md["type"] == "node":
      assert md["level"] == 0
    elif md["type"] == "edge":
      assert md["level"] == 1
    elif md["type"] == "property":
      assert md["level"] == 12
    else:
      pytest.fail()


def test_prep_sync_vector_correct_document_id(mock_repository: Mock) -> None:
  node: Node = create_basic_node(repository=mock_repository)
  edge: Edge = create_edge(repository=mock_repository, frm=node)
  prop: Property = create_property(repository=mock_repository, node=node)

  document_id: UUID = next(iter(node.metadata)).document_id

  # Set up the return values for the mock repo
  mock_repository.get_node_by_id.side_effect = [node]
  mock_repository.get_edge_by_id.side_effect = [edge]
  mock_repository.get_property_by_id.side_effect = [prop]

  change_logs: list[ChangeLog] = [
    ChangeLog(id=node.id, action=Action.CREATE, type=Node, level=4),
    ChangeLog(id=edge.id, action=Action.CREATE, type=Edge, level=4),
    ChangeLog(id=prop.id, action=Action.CREATE, type=Property, level=4),
  ]
  mock_repository.get_change_log.return_value = change_logs

  # Inject the mock repository into the function
  create_main, _ = prepare_sync_data(mock_repository)
  _, _, metadata_to_create = zip(*create_main)

  for md in metadata_to_create:
    assert md["document_id"] == str(document_id)


def test_prep_sync_vector_db_no_actions_needed() -> None:
  node_id: UUID = uuid4()
  edge_id: UUID = uuid4()
  property_id: UUID = uuid4()

  change_logs: list[ChangeLog] = [
    ChangeLog(id=edge_id, action=Action.DELETE, type=Edge, level=1),
    ChangeLog(id=edge_id, action=Action.CREATE, type=Edge, level=1),
    ChangeLog(id=property_id, action=Action.DELETE, type=Property, level=1),
    ChangeLog(id=property_id, action=Action.CREATE, type=Property, level=1),
    ChangeLog(id=node_id, action=Action.CREATE, type=Node, level=1),
    ChangeLog(id=node_id, action=Action.DELETE, type=Node, level=1),
  ]

  objects_logs: dict[UUID, list[ChangeLog]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    objects_logs[log.id].append(log)

  ids_to_create, ids_to_delete = _get_actions_for_objects(objects_logs)

  assert ids_to_create == []
  assert ids_to_delete == []


def test_prep_sync_vector_db_mixed_actions() -> None:
  node_id: UUID = uuid4()
  edge_id: UUID = uuid4()
  property_id: UUID = uuid4()

  change_logs: list[ChangeLog] = [
    ChangeLog(id=edge_id, action=Action.DELETE, type=Edge, level=1),
    ChangeLog(id=edge_id, action=Action.UPDATE, type=Edge, level=1),
    ChangeLog(id=property_id, action=Action.UPDATE, type=Property, level=1),
    ChangeLog(id=property_id, action=Action.CREATE, type=Property, level=1),
    ChangeLog(id=node_id, action=Action.UPDATE, type=Node, level=1),
    ChangeLog(id=node_id, action=Action.UPDATE, type=Node, level=1),
  ]

  objects_logs: dict[UUID, list[ChangeLog]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    objects_logs[log.id].append(log)

  ids_to_create, ids_to_delete = _get_actions_for_objects(objects_logs)

  assert set(ids_to_create) == {property_id, node_id}
  assert set(ids_to_delete) == {edge_id, node_id}


def test_get_node_document_id_level_0() -> None:
  node: Node = create_basic_node()
  document_id: UUID = next(iter(node.metadata)).document_id

  assert _get_node_document_id(node) == str(document_id)


def test_get_node_document_id_level_4() -> None:
  n0: Node = create_basic_node()
  n1: Node = create_basic_node()
  n2: Node = create_basic_node()
  n3: Node = create_basic_node()
  n4: Node = create_basic_node()

  # Setup the child-parent hierarchy
  n1.child_nodes = [n0]
  n1.level = 1
  n2.child_nodes = [n1]
  n2.level = 2
  n3.child_nodes = [n2]
  n3.level = 3
  n4.child_nodes = [n3]
  n4.level = 4

  document_id: UUID = next(iter(n0.metadata)).document_id

  assert _get_node_document_id(n4) == str(document_id)


def test_get_node_document_id_level1_no_child_nodes() -> None:
  node: Node = create_basic_node()
  node.level = 1

  document_id: UUID = next(iter(node.metadata)).document_id

  assert node.child_nodes == []
  assert _get_node_document_id(node) == str(document_id)
