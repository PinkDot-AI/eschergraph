from __future__ import annotations

from pathlib import Path
from uuid import UUID

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge
from tests.graph.persistence.adapters.simple_repository.help import (
  compare_edge_to_edge_model,
)
from tests.graph.persistence.adapters.simple_repository.help import (
  compare_node_to_node_model,
)


def test_adding_new_nodes(saved_graph_dir: Path) -> None:
  node_dict: dict[UUID, Node] = {}
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for _ in range(100):
    node: Node = create_basic_node(repository=repository)
    repository.add(node)
    node_dict[node.id] = node

  repository.save()
  del repository

  new_repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for node_id in node_dict.keys():
    assert compare_node_to_node_model(
      node=node_dict[node_id], node_model=new_repository.nodes[node_id]
    )

  assert len(new_repository.nodes) == 100


def test_adding_new_edges(saved_graph_dir: Path) -> None:
  # We add 100 edges for which the nodes are also persisted through the edges
  edge_dict: dict[UUID, Edge] = {}
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for _ in range(100):
    edge: Edge = create_edge(repository=repository)
    repository.add(edge.frm)
    repository.add(edge)
    edge_dict[edge.id] = edge

  repository.save()
  del repository

  new_repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for edge_id in edge_dict.keys():
    ref_edge: Edge = edge_dict[edge_id]
    assert compare_edge_to_edge_model(ref_edge, new_repository.edges[edge_id])
    assert compare_node_to_node_model(
      ref_edge.frm, new_repository.nodes[ref_edge.frm.id]
    )
    assert compare_node_to_node_model(ref_edge.to, new_repository.nodes[ref_edge.to.id])

  assert len(new_repository.edges) == 100
  assert len(new_repository.nodes) == 200

  for node_model in new_repository.nodes.values():
    assert len(node_model["edges"]) == 1
