from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from attrs import fields_dict

from eschergraph.exceptions import EdgeCreationException
from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState


@pytest.fixture(scope="function")
def edges_mock_repository(mock_repository: Mock) -> Mock:
  # Set the edges on the node equal to an empty set to mock the loading
  def load_side_effect(node: Node, loadstate: LoadState) -> None:
    node._edges = set()

  mock_repository.load.side_effect = load_side_effect

  return mock_repository


def test_create(edges_mock_repository: Mock) -> None:
  edge: Edge = Edge.create(
    frm=Node(repository=edges_mock_repository),
    to=Node(repository=edges_mock_repository),
    description="This is the description.",
  )
  assert edge.id

  # The edges are loaded for each node
  edges_mock_repository.load.call_count == 2


def test_create_exception(mock_repository: Mock) -> None:
  node: Node = Node(repository=mock_repository)

  with pytest.raises(EdgeCreationException):
    Edge.create(
      frm=node,
      to=node,
      description="This is the description.",
    )


def test_edge_equality(edges_mock_repository: Mock) -> None:
  node1: Node = Node(repository=edges_mock_repository)
  node2: Node = Node(repository=edges_mock_repository)
  node3: Node = Node(repository=edges_mock_repository)
  node4: Node = Node(repository=edges_mock_repository)

  edge1: Edge = Edge.create(frm=node1, to=node2, description="This is an edge")
  edge2: Edge = Edge.create(frm=node1, to=node2, description="This is an edge")
  edge3: Edge = Edge.create(frm=node2, to=node1, description="This is an edge")
  edge4: Edge = Edge.create(frm=node3, to=node4, description="This is an edge")
  edge5: Edge = Edge.create(frm=node2, to=node4, description="This is an edge")
  edge6: Edge = Edge.create(
    frm=node1,
    to=node2,
    description="This is a different edge",
  )

  assert edge1 == edge1
  assert edge1 == edge2
  assert edge1 == edge3
  assert edge2 != edge4
  assert edge2 != edge5
  assert edge1 != edge6


# Test all the added getters and setters
property_parameters: list[tuple[str, Any]] = [
  ("metadata", set()),
  ("description", "The node description"),
]


@pytest.mark.parametrize("property_parameters", property_parameters)
def test_getters(mock_repository: Mock, property_parameters: tuple[str, Any]) -> None:
  frm: Node = Node(repository=mock_repository)
  to: Node = Node(repository=mock_repository)

  attr_name, value = property_parameters

  # Set the attribute equal to a value to mock the loading
  def load_side_effect(edge: Edge, loadstate: LoadState) -> None:
    setattr(edge, "_" + attr_name, value)

  mock_repository.load.side_effect = load_side_effect
  desired_loadstate: LoadState = fields_dict(Edge)["_" + attr_name].metadata["group"]
  edge: Edge = Edge(repository=mock_repository, frm=frm, to=to)

  # Call the getter twice to assert that load is only called once
  for _ in range(2):
    assert Node.__dict__[attr_name].fget(edge) == value

  assert edge.loadstate == desired_loadstate
  mock_repository.load.assert_called_once()
  mock_repository.load.assert_called_with(edge, loadstate=desired_loadstate)


@pytest.mark.parametrize("property_parameters", property_parameters)
def test_setters(mock_repository: Mock, property_parameters: tuple[str, Any]) -> None:
  frm: Node = Node(repository=mock_repository)
  to: Node = Node(repository=mock_repository)

  attr_name, value = property_parameters

  # Set the attribute equal to a value to mock the loading
  def load_side_effect(edge: Edge, loadstate: LoadState) -> None:
    setattr(edge, "_" + attr_name, value)

  mock_repository.load.side_effect = load_side_effect
  desired_loadstate: LoadState = fields_dict(Edge)["_" + attr_name].metadata["group"]
  edge: Edge = Edge(repository=mock_repository, frm=frm, to=to)

  # Call the getter twice to assert that load is only called once
  for _ in range(2):
    Node.__dict__[attr_name].fset(edge, value)

  assert edge.loadstate == desired_loadstate
  mock_repository.load.assert_called_once()
  mock_repository.load.assert_called_with(edge, loadstate=desired_loadstate)


def test_loading_node_through_edge(mock_repository: Mock) -> None:
  # Set the attribute equal to a value to mock the loading
  def load_side_effect(object: EscherBase, loadstate: LoadState) -> None:
    if isinstance(object, Edge):
      object._description = "This is an edge description."
    elif isinstance(object, Node):
      object._name = "node_name"
      object._edges = set()

  mock_repository.load.side_effect = load_side_effect

  frm: Node = Node(repository=mock_repository)
  to: Node = Node(repository=mock_repository)
  edge: Edge = Edge(frm=frm, to=to, repository=mock_repository)

  assert not frm._name
  assert not isinstance(frm._edges, set)
  assert not edge._description

  edge.loadstate = LoadState.CORE
  assert edge._description
  assert not frm._name
  assert not isinstance(frm._edges, set)

  assert frm.name
  assert frm.loadstate == LoadState.CORE
  assert isinstance(frm.edges, set)
  assert frm.loadstate == LoadState.CONNECTED  # type: ignore
  assert to.loadstate == LoadState.REFERENCE
