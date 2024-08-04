from __future__ import annotations

import os
import pickle
from typing import Optional
from uuid import UUID

from attrs import define
from attrs import field
from attrs import fields_dict

from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.exceptions import NodeDoesNotExistException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.community import Community
from eschergraph.graph.edge import Edge
from eschergraph.graph.loading import LoadState
from eschergraph.graph.node import Node
from eschergraph.graph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.graph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.graph.persistence.exceptions import DirectoryDoesNotExistException
from eschergraph.graph.persistence.exceptions import FilesMissingException
from eschergraph.graph.persistence.exceptions import PersistenceException
from eschergraph.graph.persistence.metadata import Metadata
from eschergraph.graph.persistence.repository import Repository

# TODO: logic for loading from a file (for when the file does not yet exist)


@define
class SimpleRepository(Repository):
  """The repository implementation that stores the graph in pickled Python objects."""

  name: str = field(default=None)
  save_location: str = field(default=None)
  nodes: dict[UUID, NodeModel] = field(init=False)
  edges: dict[UUID, EdgeModel] = field(init=False)
  node_name_index: dict[str, UUID] = field(init=False)

  def __init__(
    self, name: Optional[str] = None, save_location: Optional[str] = None
  ) -> None:
    """The init method for the SimpleRepository.

    Args:
      name (Optional[str]): The graph's name.
      save_location (Optional[str]): The save location.

    """
    if not name:
      name = DEFAULT_GRAPH_NAME
    if not save_location:
      save_location = DEFAULT_SAVE_LOCATION

    self.name = name
    self.save_location = save_location

    if not os.path.isdir(save_location):
      raise DirectoryDoesNotExistException(
        f"The specified save location: {save_location} does not exist"
      )

    filenames: dict[str, str] = self._filenames(save_location, name)

    # Check if this is a new graph
    if (
      not os.path.isfile(filenames["nodes"])
      and not os.path.isfile(filenames["edges"])
      and not os.path.isfile(filenames["node_name_index"])
    ):
      self.nodes = dict()
      self.edges = dict()
      self.node_name_index = dict()
      return

    # If some files are missing
    if (
      not os.path.isfile(filenames["nodes"])
      or not os.path.isfile(filenames["edges"])
      or not os.path.isfile(filenames["node_name_index"])
    ):
      raise FilesMissingException("Some files are missing or corrupted.")

    for key, value in filenames.items():
      with open(value, "rb") as file:
        setattr(self, key, pickle.load(file))

  @staticmethod
  def _filenames(save_location: str, name: str) -> dict[str, str]:
    base_filename: str = save_location + "/" + name
    return {
      "nodes": base_filename + "-nodes.pkl",
      "edges": base_filename + "-edges.pkl",
      "node_name_index": base_filename + "-nnindex.pkl",
    }

  def load(self, object: EscherBase, loadstate: LoadState = LoadState.CORE) -> None:
    """Load the EscherBase object attributes to a certain loadstate.

    Args:
      object (EscherBase): The node or edge to load.
      loadstate (LoadState): The loadstate to load for the object. This determines
        the attributes that are loaded.
    """
    if isinstance(object, Node):
      self._load_node(node=object, loadstate=loadstate)
    elif isinstance(object, Edge):
      self._load_edge(edge=object, loadstate=loadstate)

  def _load_node(self, node: Node, loadstate: LoadState) -> None:
    # Check if the node exists in the persistence data
    if not node.id in self.nodes:
      raise PersistenceException(
        "A node with this ID does not exist in the persistent storage."
      )
    nodeModel: NodeModel = self.nodes[node.id]
    attributes: list[str] = self._select_attributes_to_load(
      object=node, loadstate=loadstate
    )
    # Load all the attributes
    for attr in attributes:
      if attr == "metadata":
        node._metadata = {Metadata(**mdt) for mdt in nodeModel["metadata"]}
      elif attr == "community":
        if nodeModel["community"]:
          # Add the reference of the community node if in a community
          node._community = Community(
            node=Node(id=nodeModel["community"], repository=node.repository)
          )
        else:
          node._community = Community()
      elif attr == "edges":
        # Add a reference to the edges
        node._edges = {
          Edge(
            id=edge["id"],
            frm=Node(id=edge["frm"], repository=node.repository),
            to=Node(id=edge["to"], repository=node.repository),
            repository=node.repository,
          )
          for edge in nodeModel["edges"]
        }
      else:
        setattr(node, "_" + attr, nodeModel[attr])  # type: ignore

  def _load_edge(self, edge: Edge, loadstate: LoadState) -> None:
    # Check if the edge exists in the persistent data
    if not edge.id in self.edges:
      raise PersistenceException(
        "An edge with this ID does not exist in the persistent storage."
      )
    edgeModel: EdgeModel = self.edges[edge.id]
    # Select the attributes that need to be loaded between the current and the needed one
    attributes: list[str] = self._select_attributes_to_load(
      object=edge, loadstate=loadstate
    )
    for attr in attributes:
      if attr == "metadata":
        edge._metadata = {Metadata(**mtd) for mtd in edgeModel["metadata"]}
      else:
        setattr(edge, "_" + attr, edgeModel[attr])  # type: ignore

    # Load the referenced nodes in the same loadstate as the edge itself
    self._load_node(edge.frm, loadstate=loadstate)
    self._load_node(edge.to, loadstate=loadstate)

  @staticmethod
  def _select_attributes_to_load(object: EscherBase, loadstate: LoadState) -> list[str]:
    attributes: list[str] = []
    for name, attr in fields_dict(object.__class__).items():
      if "group" not in attr.metadata:
        continue
      if (
        attr.metadata["group"].value > object.loadstate.value
        and attr.metadata["group"].value <= loadstate.value
      ):
        attributes.append(name)
    return attributes

  def add(self, object: EscherBase) -> None:
    """Add the node to the persistent storage.

    If it is newly created it is also created in the storage.
    If it already exists, its changes are updated.

    Args:
      object (EscherBase): The node or edge to add / update.
    """
    ...

  def get_node_by_name(self, name: str, loadstate: LoadState = LoadState.CORE) -> Node:
    """Get a node by name.

    Args:
      name (str): The name of the node.
      loadstate (LoadState): The state in which the node should be loaded.

    Returns:
      The node that matches the name.
    """
    try:
      node: Node = Node(id=self.node_name_index[name], repository=self)
      self._load_node(node, loadstate)
      return node
    except KeyError:
      raise NodeDoesNotExistException(f"No node with name: {name} exists")

  def save(self) -> None:
    """Save the graph to the persistent storage.

    Committing the graph to the secondary storage of the repository.
    This is not needed for all sorts of repositories as databases
    manage this internally.
    """
    filenames: dict[str, str] = self._filenames(self.save_location, self.name)
    for key, value in filenames.items():
      with open(value, "wb") as file:
        pickle.dump(getattr(self, key), file)
