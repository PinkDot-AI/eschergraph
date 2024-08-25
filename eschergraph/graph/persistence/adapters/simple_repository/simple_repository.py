from __future__ import annotations

import os
import pickle
from typing import cast
from typing import Optional
from uuid import UUID

from attrs import asdict
from attrs import define
from attrs import field
from attrs import fields_dict

from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.exceptions import NodeCreationException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.community import Community
from eschergraph.graph.edge import Edge
from eschergraph.graph.loading import LoadState
from eschergraph.graph.node import Node
from eschergraph.graph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.graph.persistence.adapters.simple_repository.models import (
  MetadataModel,
)
from eschergraph.graph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.graph.persistence.adapters.simple_repository.models import (
  PropertyModel,
)
from eschergraph.graph.persistence.exceptions import DirectoryDoesNotExistException
from eschergraph.graph.persistence.exceptions import FilesMissingException
from eschergraph.graph.persistence.exceptions import PersistenceException
from eschergraph.graph.persistence.exceptions import PersistingEdgeException
from eschergraph.graph.persistence.metadata import Metadata
from eschergraph.graph.persistence.repository import Repository
from eschergraph.graph.property import Property


@define
class SimpleRepository(Repository):
  """The repository implementation that stores the graph in pickled Python objects."""

  name: str = field(default=None)
  save_location: str = field(default=None)
  nodes: dict[UUID, NodeModel] = field(init=False)
  edges: dict[UUID, EdgeModel] = field(init=False)
  properties: dict[UUID, PropertyModel] = field(init=False)
  node_name_index: dict[UUID, dict[str, UUID]] = field(init=False)

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

      # Create the default directory if it does not exist
      if not os.path.isdir(save_location):
        os.makedirs(name=save_location)

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
      and not os.path.isfile(filenames["properties"])
      and not os.path.isfile(filenames["node_name_index"])
    ):
      self.nodes = dict()
      self.edges = dict()
      self.properties = dict()
      self.node_name_index = dict()
      return

    # If some files are missing
    if (
      not os.path.isfile(filenames["nodes"])
      or not os.path.isfile(filenames["edges"])
      or not os.path.isfile(filenames["properties"])
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
      "properties": base_filename + "-properties.pkl",
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
    elif isinstance(object, Property):
      self._load_property(property=object, loadstate=loadstate)

  def _load_node(self, node: Node, loadstate: LoadState) -> None:
    # Check if the node exists in the persistence data
    if not node.id in self.nodes:
      raise PersistenceException(
        "A node with this ID does not exist in the persistent storage."
      )
    node_model: NodeModel = self.nodes[node.id]
    attributes: list[str] = self._select_attributes_to_load(
      object=node, loadstate=loadstate
    )
    # Load all the attributes
    for attr in attributes:
      if attr == "metadata":
        node._metadata = {Metadata(**mdt) for mdt in node_model["metadata"]}
      elif attr == "community":
        if node_model["community"]:
          # Add the reference of the community node if in a community
          node._community = Community(
            node=Node(id=node_model["community"], repository=node.repository)
          )
        else:
          node._community = Community()
      elif attr == "edges":
        # Add a reference to the edges
        node._edges = {
          Edge(
            id=edge_id,
            frm=Node(id=self.edges[edge_id]["frm"], repository=node.repository),
            to=Node(id=self.edges[edge_id]["to"], repository=node.repository),
            repository=node.repository,
          )
          for edge_id in node_model["edges"]
        }
      elif attr == "child_nodes":
        node._child_nodes = [
          Node(id=node_id, repository=node.repository)
          for node_id in node_model["child_nodes"]
        ]
      elif attr == "properties":
        node._properties = [
          Property(id=p_id, node=node, repository=self)
          for p_id in node_model["properties"]
        ]
      else:
        setattr(node, "_" + attr, node_model[attr])  # type: ignore

  def _load_edge(self, edge: Edge, loadstate: LoadState) -> None:
    # Check if the edge exists in the persistent data
    if not edge.id in self.edges:
      raise PersistenceException(
        "An edge with this ID does not exist in the persistent storage."
      )
    edge_model: EdgeModel = self.edges[edge.id]
    # Select the attributes that need to be loaded between the current and the needed one
    attributes: list[str] = self._select_attributes_to_load(
      object=edge, loadstate=loadstate
    )
    for attr in attributes:
      if attr == "metadata":
        edge._metadata = {Metadata(**mtd) for mtd in edge_model["metadata"]}
      else:
        setattr(edge, "_" + attr, edge_model[attr])  # type: ignore

  def _load_property(self, property: Property, loadstate: LoadState) -> None:
    # Check if the property exists in the persistent data
    if not property.id in self.properties:
      raise PersistenceException(
        "A property with this ID does not exist in the persistent storage."
      )

    property_model: PropertyModel = self.properties[property.id]
    attributes: list[str] = self._select_attributes_to_load(
      object=property, loadstate=loadstate
    )
    for attr in attributes:
      if attr == "metadata":
        property._metadata = {Metadata(**mtd) for mtd in property_model["metadata"]}
      else:
        setattr(property, "_" + attr, property_model[attr])  # type: ignore

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
        attributes.append(name[1:])
    return attributes

  @staticmethod
  def _select_attributes_to_add(object: EscherBase) -> list[str]:
    attributes: list[str] = []
    for name, attr in fields_dict(object.__class__).items():
      if "group" not in attr.metadata:
        continue
      # The node id is never changed and loadstate not used
      elif attr.metadata["group"] == LoadState.REFERENCE:
        continue
      elif attr.metadata["group"].value <= object.loadstate.value:
        attributes.append(name[1:])
    return attributes

  def add(self, object: EscherBase) -> None:
    """Add the node to the persistent storage.

    If it is newly created it is also created in the storage.
    If it already exists, its changes are updated.

    Args:
      object (EscherBase): The node or edge to add / update.
    """
    if isinstance(object, Node):
      self._add_node(node=object)
    elif isinstance(object, Edge):
      self._add_edge(edge=object)
    elif isinstance(object, Property):
      self._add_property(property=object)

  def _add_node(self, node: Node) -> None:
    # Check if the node already exists
    if not node.id in self.nodes:
      self._add_new_node(node)
    else:
      attributes_to_check: list[str] = self._select_attributes_to_add(node)
      node_model: NodeModel = self.nodes[node.id]
      for attr in attributes_to_check:
        if attr == "edges":
          node_model["edges"] = {edge.id for edge in node.edges}
        elif attr == "metadata":
          node_model["metadata"] = [
            cast(MetadataModel, asdict(md)) for md in node.metadata
          ]
        elif attr == "community":
          if not node.community.node:
            node_model["community"] = None
          else:
            node_model["community"] = node.community.node.id
            self._add_node(node.community.node)
        elif attr == "child_nodes":
          node_model["child_nodes"] = {child.id for child in node.child_nodes}
        elif attr == "properties":
          node_model["properties"] = [p.id for p in node.properties]
          for property in node.properties:
            self._add_property(property=property, through_node=True)
        else:
          node_model[attr] = Node.__dict__[attr].fget(node)  # type: ignore

    # Adding the nodes (without edges) that are connected to this node
    for edge in node.edges:
      if not edge.frm.id in self.nodes:
        self._add_new_node(node=edge.frm, add_edges=False)
      elif not edge.to.id in self.nodes:
        self._add_new_node(node=edge.to, add_edges=False)

      self._add_edge(edge)

    # Adding the child nodes (without edges)
    for child in node.child_nodes:
      if not child.id in self.nodes:
        self._add_new_node(node=child, add_edges=False)

  def _add_new_node(self, node: Node, add_edges: bool = True) -> None:
    if not node.loadstate == LoadState.FULL:
      raise PersistenceException("A newly created node should be fully loaded.")

    # Check if the node already exists for this document
    if node.level == 0:
      for mtd in node.metadata:
        if self.get_node_by_name(name=node.name, document_id=mtd.document_id):
          raise NodeCreationException(
            f"A node with name: {node.name} already exists at level 0 for this document"
          )
    node_model: NodeModel = self._new_node_to_node_model(node)
    if not add_edges:
      node_model["edges"] = set()
    self.nodes[node.id] = node_model

    # Add the properties
    for prop in node.properties:
      self._add_property(property=prop, through_node=True)

    # Keep the node-name index updated
    for mtd in node.metadata:
      if not mtd.document_id in self.node_name_index:
        self.node_name_index[mtd.document_id] = {}

      self.node_name_index[mtd.document_id][node.name] = node.id

  def _add_property(self, property: Property, through_node: bool = False) -> None:
    # Check if the property has been added to the repository directly
    if not through_node and not property.node.id in self.nodes:
      raise PersistenceException(
        "The referenced node in a property needs to exist when a property is persisted directly."
      )

    if not property.id in self.properties:
      new_model: PropertyModel = self._new_property_to_property_model(property)
      self.properties[property.id] = new_model

      # Only add to the node's properties if not called from a node
      if not through_node:
        self.nodes[property.node.id]["properties"].append(property.id)
    else:
      property_model: PropertyModel = self.properties[property.id]
      attributes: list[str] = self._select_attributes_to_add(property)
      for attr in attributes:
        if attr == "metadata":
          property_model["metadata"] = [
            cast(MetadataModel, asdict(md)) for md in property.metadata
          ]
        else:
          property_model[attr] = Node.__dict__[attr].fget(property)  # type: ignore

  @staticmethod
  def _new_node_to_node_model(node: Node) -> NodeModel:
    return {
      "name": node.name,
      "description": node.description,
      "level": node.level,
      "properties": [p.id for p in node.properties],
      "edges": {edge.id for edge in node.edges},
      "community": node.community.node.id if node.community.node else None,
      "metadata": [cast(MetadataModel, asdict(md)) for md in node.metadata],
      "child_nodes": {child.id for child in node.child_nodes},
    }

  @staticmethod
  def _new_edge_to_edge_model(edge: Edge) -> EdgeModel:
    return {
      "frm": edge.frm.id,
      "to": edge.to.id,
      "description": edge.description,
      "metadata": [cast(MetadataModel, asdict(md)) for md in edge.metadata],
    }

  @staticmethod
  def _new_property_to_property_model(property: Property) -> PropertyModel:
    return {
      "node": property.node.id,
      "description": property.description,
      "metadata": [cast(MetadataModel, asdict(md)) for md in property.metadata],
    }

  def _add_edge(self, edge: Edge) -> None:
    # Check if both referenced nodes are already persisted
    if not edge.frm.id in self.nodes or not edge.to.id in self.nodes:
      raise PersistingEdgeException(
        "Both referenced nodes need to exist when an edge is persisted directly"
      )

    # Check if the edge already exists
    if not edge.id in self.edges:
      self.edges[edge.id] = self._new_edge_to_edge_model(edge)

      # Making sure that the edges can also be found on the nodes
      self.nodes[edge.frm.id]["edges"].add(edge.id)
      self.nodes[edge.to.id]["edges"].add(edge.id)
    else:
      attributes_to_check: list[str] = self._select_attributes_to_add(edge)
      edge_model: EdgeModel = self.edges[edge.id]
      for attr in attributes_to_check:
        if attr == "frm":
          edge_model["frm"] = edge.frm.id
        elif attr == "to":
          edge_model["to"] = edge.to.id
        elif attr == "description":
          edge_model["description"] = edge.description
        elif attr == "metadata":
          edge_model["metadata"] = [
            cast(MetadataModel, asdict(md)) for md in edge.metadata
          ]

  def get_node_by_name(
    self, name: str, document_id: UUID, loadstate: LoadState = LoadState.CORE
  ) -> Optional[Node]:
    """Get a node from a certain document by name.

    Returns the node, and None if no node is found.
    The nodes that are returned from this method are all at level 0.

    Args:
      name (str): The node to get.
      document_id (UUID): The id of the document from which the node has been extracted.
      loadstate (LoadState): The state in which the node should be loaded.

    Returns:
      The node that matches the name in the specified document.
    """
    if not document_id in self.node_name_index:
      return None
    id: Optional[UUID] = self.node_name_index[document_id].get(name)
    if not id:
      return None
    node_id: UUID = id
    node: Node = Node(id=node_id, repository=self)
    self._load_node(node, loadstate)
    return node

  def get_node_by_id(self, id: UUID) -> Optional[Node]:
    """Get a node by id.

    If a node with this id is not found, then None is returned.

    Args:
      id (UUID): The node's id.

    Returns:
      The node or None if no node with this id exists.
    """
    if not id in self.nodes:
      return None
    return Node(id=id, repository=self)

  def get_edge_by_id(self, id: UUID) -> Optional[Edge]:
    """Get an edge by id.

    If no edge with this id is found, then None is returned.

    Args:
      id (UUID): The edge's id.

    Returns:
      The edge or None if no edge is found.
    """
    edge_model: Optional[EdgeModel] = self.edges.get(id)
    if not edge_model:
      return None
    return Edge(
      id=id,
      frm=Node(id=edge_model["frm"], repository=self),
      to=Node(id=edge_model["to"], repository=self),
      repository=self,
    )

  def get_property_by_id(self, id: UUID) -> Optional[Property]:
    """Get a property by id.

    If no property with this id is found, then None is returned.

    Args:
      id (UUID): The property's id.

    Returns:
      The property of None if no property is found.
    """
    property_model: Optional[PropertyModel] = self.properties.get(id)
    if not property_model:
      return None
    else:
      return Property(
        id=id, node=Node(id=property_model["node"], repository=self), repository=self
      )

  def get_all_at_level(self, level: int) -> list[Node]:
    """Get all nodes at a certain level.

    Note that level 0 corresponds to nodes that are directly extracted
    from a source text. Level 1 corresponds to the direct communities of these nodes.
    And so on.

    Args:
      level (int): The level at which the nodes should occur.

    Returns:
      A list with all the nodes at the specified level.
    """
    return [
      Node(id=id, repository=self)
      for id, nm in self.nodes.items()
      if nm["level"] == level
    ]

  def get_max_level(self) -> int:
    """Get the highest non-root level of the graph.

    Returns:
        int: The highest level
    """
    return max(node["level"] for node in self.nodes.values())

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
