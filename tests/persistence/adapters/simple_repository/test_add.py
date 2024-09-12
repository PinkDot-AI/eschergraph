from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

from eschergraph.exceptions import NodeCreationException
from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.loading import LoadState
from eschergraph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.persistence.exceptions import PersistenceException
from eschergraph.persistence.exceptions import PersistingEdgeException
from tests.graph.help import create_basic_node
from tests.graph.help import create_edge
from tests.persistence.adapters.simple_repository.help import (
  compare_edge_to_edge_model,
)
from tests.persistence.adapters.simple_repository.help import (
  compare_node_to_node_model,
)


def test_adding_new_nodes(saved_graph_dir: Path) -> None:
  node_dict: dict[UUID, Node] = {}
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for _ in range(10):
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

  assert len(new_repository.nodes) == 10


def test_adding_duplicate_node_name_document(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  node1: Node = create_basic_node(repository=repository)
  node2: Node = create_basic_node(repository=repository)

  # Make sure that node 2 duplicates node 1
  node2.name = node1.name
  node2.metadata = node1.metadata

  repository.add(node1)

  with pytest.raises(NodeCreationException):
    repository.add(node2)


def test_adding_new_edges(saved_graph_dir: Path) -> None:
  # We add 100 edges for which the nodes are also persisted through the edges
  edge_dict: dict[UUID, Edge] = {}
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for _ in range(10):
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

  assert len(new_repository.edges) == 10
  assert len(new_repository.nodes) == 20

  for node_model in new_repository.nodes.values():
    assert len(node_model["edges"]) == 1


def test_adding_edges_without_nodes(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  with pytest.raises(PersistingEdgeException):
    repository.add(create_edge())


def test_adding_new_node_wrong_loadstate(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  node: Node = create_basic_node(repository=repository)
  node._loadstate = LoadState.CORE

  with pytest.raises(PersistenceException):
    repository.add(node)


def test_adding_nodes_with_and_without_edges(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  node_frm: Node = create_basic_node(repository=repository)
  node_to: Node = create_basic_node(repository=repository)
  edge_added: Edge = create_edge(frm=node_frm, to=node_to, repository=repository)

  assert len(node_frm.edges) == 1
  assert len(node_to.edges) == 1
  assert node_to.edges == node_frm.edges

  repository._add_new_node(node_frm, add_edges=False)
  assert repository.nodes[node_frm.id]["edges"] == set()

  repository._add_new_node(node_to)
  assert repository.nodes[node_to.id]["edges"] == {edge_added.id}


def test_adding_nodes_connected_to_node_added(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  node_frm: Node = create_basic_node(repository=repository)
  node_to: Node = create_basic_node(repository=repository)
  node_extra: Node = create_basic_node(repository=repository)
  edge_in_scope: Edge = create_edge(frm=node_frm, to=node_to, repository=repository)
  create_edge(frm=node_extra, to=node_to, repository=repository)

  repository.add(node_frm)

  assert len(repository.edges) == 1
  assert edge_in_scope.id in repository.edges
  assert node_to.id in repository.nodes
  assert not node_extra.id in repository.nodes
  assert repository.nodes[node_to.id]["edges"] == {edge_in_scope.id}


def test_adding_nodes_through_connected_edges(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  node1: Node = create_basic_node(repository=repository)
  node2: Node = create_basic_node(repository=repository)
  node3: Node = create_basic_node(repository=repository)

  edge1: Edge = create_edge(frm=node1, to=node2)
  edge2: Edge = create_edge(frm=node2, to=node3)

  repository.add(node1)

  # Check if node 2 is only added with its edge to node1
  node2_per: Node | None = repository.get_node_by_id(id=node2.id)

  if not node2_per:
    pytest.fail()

  assert edge1.id in repository.edges
  assert node2_per.edges == {edge1}

  repository.add(node2)

  # Check if all node2's edges are now added
  node2_full: Node | None = repository.get_node_by_id(id=node2.id)
  node3_per: Node | None = repository.get_node_by_id(id=node3.id)

  if not node2_full or not node3_per:
    pytest.fail()

  assert node2_full.edges == {edge1, edge2}
  assert node3.edges == {edge2}
  assert edge2.id in repository.edges
