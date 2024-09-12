from __future__ import annotations

import random
from typing import Any
from unittest.mock import call
from unittest.mock import Mock
from uuid import UUID
from uuid import uuid4

import pytest
from attrs import fields_dict

from eschergraph.exceptions import NodeCreationException
from eschergraph.graph import Node
from eschergraph.graph.community import Community
from eschergraph.graph.loading import LoadState
from eschergraph.persistence import Metadata


def test_initialize(mock_repository: Mock) -> None:
  assert Node(repository=mock_repository).id


def test_create(mock_repository: Mock) -> None:
  node: Node = Node.create(
    name="test_node",
    description="A node for testing",
    level=1,
    repository=mock_repository,
  )
  assert node.properties == []
  assert node.id
  assert node.level == 1
  assert node.edges == set()
  assert node.child_nodes == []
  assert node.loadstate == LoadState.FULL

  # No loading is conducted for a new node (not at level 0)
  mock_repository.load.assert_not_called()


def test_create_level_0_no_metadata(mock_repository: Mock) -> None:
  with pytest.raises(NodeCreationException):
    Node.create(
      name="test_node",
      description="A node for testing",
      level=0,
      repository=mock_repository,
    )


def test_create_level_0_no_same_name(mock_repository: Mock) -> None:
  # Prepare the mock
  mock_repository.get_node_by_name.return_value = None

  document_id: UUID = uuid4()
  node: Node = Node.create(
    name="test_node",
    description="A node for testing",
    level=0,
    repository=mock_repository,
    metadata={Metadata(document_id=document_id, chunk_id=1)},
  )

  mock_repository.get_node_by_name.assert_called_once_with(
    name=node.name, document_id=document_id
  )


def test_create_level_0_same_name(mock_repository: Mock) -> None:
  document_id: UUID = uuid4()
  duplicate_node: Node = Node(
    metadata={Metadata(document_id=document_id, chunk_id=1)},
    name="test_node",
    description="the original node",
    level=0,
    repository=mock_repository,
    properties=[],
    loadstate=LoadState.CORE,
  )
  mock_repository.get_node_by_name.return_value = duplicate_node
  node: Node = Node.create(
    name="test_node",
    description="A node for testing",
    level=0,
    repository=mock_repository,
    metadata={Metadata(document_id=document_id, chunk_id=2)},
  )

  mock_repository.get_node_by_name.assert_called_once()
  node.name == "test_node"
  node.id == duplicate_node.id
  node.metadata = {
    Metadata(document_id=document_id, chunk_id=2),
    Metadata(document_id=document_id, chunk_id=1),
  }


# Test all the added getters and setters
property_parameters: list[tuple[str, Any]] = [
  ("metadata", set()),
  ("name", "node_name"),
  ("description", "The node description"),
  ("level", 1),
  ("properties", []),
  ("edges", set()),
  ("community", Community()),
  ("child_nodes", []),
]


@pytest.mark.parametrize("property_parameters", property_parameters)
def test_getters(mock_repository: Mock, property_parameters: tuple[str, Any]) -> None:
  attr_name, value = property_parameters

  # Set the attribute equal to a value to mock the loading
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

  # Set the attribute equal to a value to mock the loading
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


# A test that checks whether the loadstate logic is correct and can only be increased
@pytest.mark.repeat(5)
def test_check_loadstate_logic(mock_repository: Mock) -> None:
  def load_side_effect(node: Node, loadstate: LoadState) -> None:
    for attr_name, value in property_parameters:
      setattr(node, "_" + attr_name, value)

  mock_repository.load.side_effect = load_side_effect
  node: Node = Node(repository=mock_repository)

  # Keeping track of the test evolution
  max_loadstate: LoadState = LoadState.REFERENCE
  calls: list[Any] = []

  # Make 20 random getter calls
  for _ in range(20):
    idx: int = random.randint(0, len(property_parameters) - 1)
    attr_name, _ = property_parameters[idx]
    Node.__dict__[attr_name].fget(node)
    needed_loadstate: LoadState = fields_dict(Node)["_" + attr_name].metadata["group"]

    # If more needs to be loaded
    if needed_loadstate.value > max_loadstate.value:
      max_loadstate = needed_loadstate
      calls.append(call(node, loadstate=needed_loadstate))

  assert node.loadstate == max_loadstate
  mock_repository.load.assert_has_calls(calls)
