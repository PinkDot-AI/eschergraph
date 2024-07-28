from __future__ import annotations

from eschergraph.graph import Node


def create_mock_node() -> Node:
  return Node(name="test-node", description="A node for testing.", level=0)


def test_node_persistence_attributes() -> None:
  node: Node = create_mock_node()
  print(node.persisted)
  node.child_nodes
