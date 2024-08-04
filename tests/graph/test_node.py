from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from attrs import fields_dict

from eschergraph.graph import Node
from eschergraph.graph.community import Community
from eschergraph.graph.loading import LoadState


def test_initialize(mock_repository: Mock) -> None:
  assert Node(repository=mock_repository).id


def test_create_node(mock_repository: Mock) -> None:
  node: Node = Node.create_node(
    name="test_node",
    description="A node for testing",
    level=0,
    repository=mock_repository,
  )
  assert node.properties == []
  assert node.id
  assert node.level == 0
  assert node.edges == set()
  assert node.report == []
  assert node.child_nodes == []
  assert node.loadstate == LoadState.FULL


# Test all the added getters and setters
property_parameters: list[tuple[str, Any]] = [
  ("metadata", set()),
  ("name", "node_name"),
  ("description", "The node description"),
  ("level", 1),
  ("properties", ["important", "large"]),
  ("edges", set()),
  ("community", Community()),
  ("child_nodes", []),
  ("report", []),
]


@pytest.mark.parametrize("property_parameters", property_parameters)
def test_getters(mock_repository: Mock, property_parameters: tuple[str, Any]) -> None:
  attr_name, value = property_parameters

  # set the attribute equal to a value to mock the loading
  def load_side_effect(node: Node, loadstate: LoadState) -> None:
    setattr(node, "_" + attr_name, value)

  mock_repository.load.side_effect = load_side_effect
  desired_loadstate: LoadState = fields_dict(Node)["_" + attr_name].metadata["group"]
  node: Node = Node(repository=mock_repository)

  # Call the getter twice to assert that load is only called once
  for _ in range(2):
    assert Node.__dict__[attr_name].fget(node) == value

  assert node.loadstate == desired_loadstate
  mock_repository.load.assert_called_once()
  mock_repository.load.assert_called_with(node, loadstate=desired_loadstate)


@pytest.mark.parametrize("property_parameters", property_parameters)
def test_setters(mock_repository: Mock, property_parameters: tuple[str, Any]) -> None:
  attr_name, value = property_parameters

  # set the attribute equal to a value to mock the loading
  def load_side_effect(node: Node, loadstate: LoadState) -> None:
    setattr(node, "_" + attr_name, value)

  mock_repository.load.side_effect = load_side_effect
  desired_loadstate: LoadState = fields_dict(Node)["_" + attr_name].metadata["group"]
  node: Node = Node(repository=mock_repository)

  # Call the setter twice to assert that load is only called once
  for _ in range(2):
    Node.__dict__[attr_name].fset(node, value)

  assert node.loadstate == desired_loadstate
  mock_repository.load.assert_called_once()
  mock_repository.load.assert_called_with(node, loadstate=desired_loadstate)
