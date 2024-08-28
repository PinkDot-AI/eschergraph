from __future__ import annotations

from unittest.mock import Mock

from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence.change_log import Action
from eschergraph.graph.persistence.change_log import ChangeLog
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
