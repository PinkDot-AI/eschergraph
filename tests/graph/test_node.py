from __future__ import annotations

from uuid import UUID

from eschergraph.graph import Node


def create_mock_node() -> Node:
  return Node(name="test-node", description="A node for testing.", level=0)


def test_node_persistence_attributes() -> None:
  node: Node = create_mock_node()

  assert node.id is not None
  assert type(node.id) == UUID
  assert node.persisted == False
  assert node.loaded == True


def test_node_id_generation() -> None:
  node1: Node = create_mock_node()
  node2: Node = create_mock_node()

  assert node1.id != node2.id
