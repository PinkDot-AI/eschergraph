from __future__ import annotations

from pathlib import Path
from uuid import UUID
from uuid import uuid4

import pytest

from eschergraph.exceptions import NodeDoesNotExistException
from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.document import DocumentData
from tests.graph.help import create_simple_extracted_graph


def test_delete_node(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  _, nodes, _ = create_simple_extracted_graph(repository=repository)
  node_to_delete: Node = nodes[0]
  repository.remove_node_by_id(node_to_delete.id)

  assert not node_to_delete.id in repository.nodes
  assert not repository.get_node_by_id(node_to_delete.id)

  # Check all the properties of the deleted node
  for prop in node_to_delete.properties:
    assert not prop.id in repository.properties
    assert not repository.get_property_by_id(prop.id)

  # Check all the nodes
  for edge in node_to_delete.edges:
    assert not edge.id in repository.edges
    assert not repository.get_edge_by_id(edge.id)

    # Check that the edge has been deleted from the other node
    edge_node_ids: set[UUID] = {edge.frm.id, edge.to.id}
    edge_node_ids.remove(node_to_delete.id)
    other_node_id: UUID = edge_node_ids.pop()
    other_node: Node | None = repository.get_node_by_id(other_node_id)
    assert other_node
    assert not edge.id in {e.id for e in other_node.edges}


def test_delete_node_does_not_exist(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  with pytest.raises(NodeDoesNotExistException):
    repository.remove_node_by_id(uuid4())


def test_delete_edge_indirectly(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  _, _, edges = create_simple_extracted_graph(repository=repository)
  node: Node = edges[0].frm
  edge_deleted: Edge = node.edges.pop()
  repository.add(node)

  assert not edge_deleted in node.edges
  assert not edge_deleted.id in repository.edges
  assert not repository.get_edge_by_id(edge_deleted.id)

  # Check whether it has been deleted from the other node
  edge_node_ids: set[UUID] = {edge_deleted.to.id, edge_deleted.frm.id}
  edge_node_ids.remove(node.id)
  other_node: Node = repository.get_node_by_id(edge_node_ids.pop())

  assert not edge_deleted in other_node.edges


def test_delete_property_indirectly(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  _, nodes, _ = create_simple_extracted_graph(repository=repository)
  node: Node = nodes[0]
  property_deleted: Property = node.properties.pop()
  repository.add(node)

  assert not property_deleted.id in repository.properties
  assert not repository.get_property_by_id(property_deleted.id)
  assert not property_deleted in repository.get_node_by_id(node.id).properties


def test_delete_document_fully(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  _, nodes1, edges1 = create_simple_extracted_graph(repository=repository)
  _, nodes2, _ = create_simple_extracted_graph(repository=repository)

  # Check whether the test has been set up correctly
  assert {n.id for n in nodes1} | {n.id for n in nodes2} == {
    n.id for n in repository.get_all_at_level(0)
  }

  document_id1: UUID = next(iter(nodes1[0].metadata)).document_id
  document_id2: UUID = next(iter(nodes2[0].metadata)).document_id

  # Add both documents
  repository.add_document(
    DocumentData(id=document_id1, name="doc1", chunk_num=100, token_num=100)
  )
  repository.add_document(
    DocumentData(id=document_id2, name="doc2", chunk_num=100, token_num=100)
  )

  repository.remove_document_by_id(document_id1)
  deleted_edge_ids: list[UUID] = [edge.id for edge in edges1]
  deleted_prop_ids: list[UUID] = [
    prop.id for node in nodes1 for prop in node.properties
  ]

  assert {n.id for n in nodes2} == {n.id for n in repository.get_all_at_level(0)}
  for edge_id in deleted_edge_ids:
    assert not edge_id in repository.edges
    assert not repository.get_edge_by_id(edge_id)
  for prop_id in deleted_prop_ids:
    assert not prop_id in repository.properties
    assert not repository.get_property_by_id(prop_id)
