from __future__ import annotations

from eschergraph.graph import Edge
from eschergraph.graph import Node
from tests.graph.test_node import create_node


def create_edge() -> Edge:
  frm: Node = create_node()
  frm.name = "The from node"
  to: Node = create_node()
  to.name = "The to node"

  return Edge(to=to, frm=frm, description="The edge for testing")


def test_edge_hash() -> None:
  edge: Edge = create_edge()

  assert isinstance(hash(edge), int)


def test_edge_hash_unequal() -> None:
  edge1: Edge = create_edge()
  edge2: Edge = create_edge()
  edge2.description = "The second edge"

  assert hash(edge1) != hash(edge2)
