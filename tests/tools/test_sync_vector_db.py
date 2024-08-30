from __future__ import annotations

from unittest.mock import Mock
from uuid import UUID
from uuid import uuid4

import pytest

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.graph.persistence.change_log import Action
from eschergraph.graph.persistence.change_log import ChangeLog
from eschergraph.tools.prepare_sync_data import _get_actions_for_objects
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
  create_main, create_node_name, ids_to_delete, delete_node_name_ids = (
    prepare_sync_data(mock_repository)
  )

  ids_to_create, docs_to_create, metadata_to_create = zip(*create_main)
  ids_to_create_node, node_to_create, metadata_to_create_node = zip(*create_node_name)

  assert set(ids_to_create) == {node1.id, node2.id, edge1.id, prop1.id}
  assert set(ids_to_delete) == {node2.id, prop1.id}
  assert set(docs_to_create) == {
    node1.description,
    node2.description,
    edge1.description,
    prop1.description,
  }

  assert set(node_to_create) == {node1.name, node2.name}
  assert set(delete_node_name_ids) == {node2.id}
  assert set(ids_to_create_node) == {node1.id, node2.id}

  # Assert the correct metadata
  for md in metadata_to_create:
    if md["type"] == "node":
      assert md["entity_frm"] in [node1.name, node2.name]
      assert md["entity_to"] == ""
    elif md["type"] == "edge":
      assert md["entity_frm"] == edge1.frm.name
      assert md["entity_to"] == edge1.to.name
    elif md["type"] == "property":
      assert md["entity_frm"] == prop1.node.name
      assert md["entity_to"] == ""
    elif md["type"] == "node_name":
      assert md["entity_frm"] in [node1.name, node2.name]
      assert md["entity_to"] == ""
    else:
      pytest.fail()


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
