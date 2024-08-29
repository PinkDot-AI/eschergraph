from __future__ import annotations

from unittest.mock import Mock
from uuid import UUID
from uuid import uuid4

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.graph.persistence.change_log import Action
from eschergraph.graph.persistence.change_log import ChangeLog
from eschergraph.tools.prepare_sync_data import _get_actions_for_objects
from eschergraph.tools.prepare_sync_data import prepare_sync_data
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge


def test_prep_sync_vector_db(mock_repository: Mock) -> None:
  # Mock the repository
  node1 = create_basic_node(mock_repository)
  node2 = create_basic_node(mock_repository)
  edge1 = create_edge(repository=mock_repository)
  edge2 = create_edge(repository=mock_repository)

  change_logs: list[ChangeLog] = [
    ChangeLog(id=node1.id, action=Action.CREATE, type=Node, level=0),
    ChangeLog(id=node2.id, action=Action.UPDATE, type=Node, level=0),
    ChangeLog(id=edge1.id, action=Action.CREATE, type=Edge, level=0),
    ChangeLog(id=edge2.id, action=Action.DELETE, type=Edge, level=0),
  ]
  mock_repository.get_change_log.return_value = change_logs

  # Inject the mock repository into the function
  _, ids, metadata, ids_to_delete = prepare_sync_data(mock_repository)
  # Assertions
  assert len(ids_to_delete) == 2
  assert len(ids) == 3
  assert metadata[0]["type"] == "node"
  assert metadata[1]["type"] == "node"
  assert metadata[2]["type"] == "edge"


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
