from __future__ import annotations

import itertools
import os
import pickle
from typing import cast
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import asdict
from attrs import define
from attrs import field
from attrs import fields_dict

from eschergraph.builder.build_log import BuildLog
from eschergraph.config import DEFAULT_GRAPH_NAME
from eschergraph.config import DEFAULT_SAVE_LOCATION
from eschergraph.exceptions import DocumentDoesNotExistException
from eschergraph.exceptions import NodeCreationException
from eschergraph.exceptions import NodeDoesNotExistException
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
from eschergraph.graph.persistence.change_log import Action
from eschergraph.graph.persistence.change_log import ChangeLog
from eschergraph.graph.persistence.document import DocumentData
from eschergraph.graph.persistence.exceptions import DirectoryDoesNotExistException
from eschergraph.graph.persistence.exceptions import FilesMissingException
from eschergraph.graph.persistence.exceptions import PersistenceException
from eschergraph.graph.persistence.exceptions import PersistingEdgeException
from eschergraph.graph.persistence.metadata import Metadata
from eschergraph.graph.persistence.repository import Repository
from eschergraph.graph.property import Property

if TYPE_CHECKING:
  from eschergraph.graph.base import EscherBase
  from eschergraph.builder.build_log import BuildLog


@define
class SimpleRepository(Repository):
  """The repository implementation that stores the graph in pickled Python objects."""

  name: str = field(default=None)
  save_location: str = field(default=None)
  nodes: dict[UUID, NodeModel] = field(init=False)
  edges: dict[UUID, EdgeModel] = field(init=False)
  properties: dict[UUID, PropertyModel] = field(init=False)
  doc_node_name_index: dict[UUID, dict[str, UUID]] = field(init=False)
  change_log: list[ChangeLog] = field(init=False)
  documents: dict[UUID, DocumentData] = field(init=False)
  original_build_logs: dict[UUID, list[BuildLog]] = field(init=False)

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

    # Initialize the (empty) changelog
    self.change_log = []

    if not os.path.isdir(save_location):
      raise DirectoryDoesNotExistException(
        f"The specified save location: {save_location} does not exist"
      )

    filenames: dict[str, str] = self._filenames(save_location, name)
    new_graph: bool = True
    all_files: bool = True

    # Check if this is a new graph and if all files are present
    for filename in filenames.values():
      if os.path.isfile(filename):
        new_graph = False
      if not os.path.isfile(filename):
        all_files = False

    if new_graph:
      self.nodes = dict()
      self.edges = dict()
      self.properties = dict()
      self.doc_node_name_index = dict()
      self.documents = dict()
      self.original_build_logs = dict()
      return

    # If some files are missing
    if not all_files:
      raise FilesMissingException("Some files are missing or corrupted.")

    # Load existing data
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
      "doc_node_name_index": base_filename + "-nnindex.pkl",
      "documents": base_filename + "-documents.pkl",
      "original_build_logs": base_filename + "-ogbuidlogs.pkl",
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
    # Keep track of the old name for the (doc) node name index
    old_name: str = ""
    # Check if the node already exists
    if not node.id in self.nodes:
      self._add_new_node(node)
    else:
      attributes_to_check: list[str] = self._select_attributes_to_add(node)
      self.change_log.append(
        ChangeLog(
          id=node.id,
          action=Action.UPDATE,
          type=Node,
          attributes=attributes_to_check,
          level=node.level,
        )
      )
      node_model: NodeModel = self.nodes[node.id]
      for attr in attributes_to_check:
        if attr == "edges":
          # Also allows for edges to be altered / deleted through a node
          removed_edges: set[UUID] = node_model["edges"].difference({
            edge.id for edge in node.edges
          })
          for edge_id in removed_edges:
            self._remove_edge(
              edge_model=self.edges[edge_id], edge_id=edge_id, through_node=node.id
            )

          # Update the edges on the node
          node_model["edges"] = {edge.id for edge in node.edges}

          # Persist the changes made to the edge itself
          for edge in node.edges:
            self._add_edge(edge)
        elif attr == "metadata":
          # Update the node name index if the metadata changes
          if (old_doc_ids := {md["document_id"] for md in node_model["metadata"]}) != (
            new_doc_ids := {md.document_id for md in node.metadata}
          ):
            # Remove the old node name index values
            for doc_id in old_doc_ids:
              del self.doc_node_name_index[doc_id][node_model["name"]]

            # Add the new node name index values
            for doc_id in new_doc_ids:
              self.doc_node_name_index[doc_id][node_model["name"]] = node.id
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
          # Also allow for properties to be altered / deleted through a node
          removed_properties: set[UUID] = set(node_model["properties"]).difference({
            prop.id for prop in node.properties
          })
          for prop_id in removed_properties:
            self._remove_property(id=prop_id, property_model=self.properties[prop_id])

          # Update the properties on the node
          node_model["properties"] = [p.id for p in node.properties]

          # Persist the properties themselves
          for property in node.properties:
            self._add_property(property=property, through_node=True)
        elif attr == "name":
          name_changed: bool = node_model["name"] == node.name
          if name_changed:
            old_name = node_model["name"]
            node_model["name"] = node.name
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

    # Update the doc node name index
    if old_name:
      for doc_id in {md["document_id"] for md in node_model["metadata"]}:
        del self.doc_node_name_index[doc_id][old_name]
        self.doc_node_name_index[doc_id][node.name] = node.id

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
      if not mtd.document_id in self.doc_node_name_index:
        self.doc_node_name_index[mtd.document_id] = {}

      self.doc_node_name_index[mtd.document_id][node.name] = node.id

    # Log the addition of a new node
    self.change_log.append(
      ChangeLog(id=node.id, action=Action.CREATE, type=Node, level=node.level)
    )

    # Log the addition of a new node
    self.change_log.append(
      ChangeLog(id=node.id, action=Action.CREATE, type=Node, level=node.level)
    )

  def _add_property(self, property: Property, through_node: bool = False) -> None:
    # Check if the property has been added to the repository directly
    if not through_node and not property.node.id in self.nodes:
      raise PersistenceException(
        "The referenced node in a property needs to exist when a property is persisted directly."
      )

    if not property.id in self.properties:
      if not property.loadstate == LoadState.FULL:
        raise PersistenceException("A newly created property should be fully loaded.")

      new_model: PropertyModel = self._new_property_to_property_model(property)
      self.properties[property.id] = new_model
      self.change_log.append(
        ChangeLog(
          id=property.id, action=Action.CREATE, type=Property, level=property.node.level
        )
      )

      # Only add to the node's properties if not called from a node
      if not through_node:
        self.nodes[property.node.id]["properties"].append(property.id)
    else:
      property_model: PropertyModel = self.properties[property.id]
      attributes: list[str] = self._select_attributes_to_add(property)
      self.change_log.append(
        ChangeLog(
          id=property.id,
          action=Action.UPDATE,
          type=Property,
          attributes=attributes,
          level=property.node.level,
        )
      )
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
      self.change_log.append(
        ChangeLog(id=edge.id, action=Action.CREATE, type=Edge, level=edge.frm.level)
      )

      # Making sure that the edges can also be found on the nodes
      self.nodes[edge.frm.id]["edges"].add(edge.id)
      self.nodes[edge.to.id]["edges"].add(edge.id)
    else:
      attributes_to_check: list[str] = self._select_attributes_to_add(edge)
      self.change_log.append(
        ChangeLog(
          id=edge.id,
          action=Action.UPDATE,
          type=Edge,
          attributes=attributes_to_check,
          level=edge.frm.level,
        )
      )
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
    if not document_id in self.doc_node_name_index:
      return None
    id: Optional[UUID] = self.doc_node_name_index[document_id].get(name)
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

  def get_change_log(self) -> list[ChangeLog]:
    """Get the list of change logs.

    The logs contain all the add operations that are performed for
    EscherBase objects. These can be used to sync other systems such as
    the vector database.

    Returns:
      A list of all changelogs.
    """
    return self.change_log

  def clear_change_log(self) -> None:
    """Clear all change logs.

    Use with caution. Should only be performed after syncing to external
    systems such as a vector database.
    """
    self.change_log = []

  def add_document(self, document_data: DocumentData) -> None:
    """Adds a document to the system.

    If a document with the same ID already exists, then the existing
    data will be overwritten with the specified object.

    Args:
      document_data (DocumentData): The document data that needs to be added.
    """
    self.documents[document_data.id] = document_data

    # If the document does not yet exist, add to document node name index
    if not (doc_id := document_data.id) in self.doc_node_name_index:
      self.doc_node_name_index[doc_id] = {}

  def get_documents_by_id(self, ids: list[UUID]) -> list[DocumentData]:
    """Retrieves documents based on a list of document UUIDs.

    Args:
      ids (list[UUID]): A list of UUIDs representing the documents to be fetched.

    Returns:
      list[DocumentData]: A list of DocumentData instances for the requested documents.
    """
    doc_result: list[DocumentData] = []
    for doc_id in ids:
      document: DocumentData | None = self.documents.get(doc_id)

      if document:
        doc_result.append(document)

    return doc_result

  def add_original_build_logs(self, original_build_logs: list[BuildLog]) -> None:
    """Add the original build logs for storage.

    The original build logs are used for the evaluation that calculates
    a loss of information score. Original refers to the build logs from before
    applying the node matcher. Note that the build logs are stored for each document.
    If the build logs for a document do already exist, then they are overwritten.

    Args:
      original_build_logs (list[BuildLog]): A list of build logs.
    """
    docs_encountered: set[UUID] = set()
    for log in original_build_logs:
      if not (document_id := log.metadata.document_id) in docs_encountered:
        self.original_build_logs[document_id] = [log]
        docs_encountered.add(document_id)
      else:
        self.original_build_logs[document_id].append(log)

  def get_original_build_logs_by_document_id(self, document_id: UUID) -> list[BuildLog]:
    """Get the original build logs by document_id.

    The original build logs are used for the evaluation that calculates
    a loss of information score. Original refers to the build logs from before
    applying the node matcher.

    Args:
     document_id (UUID): The document to get the original build logs for, specified
       by its id.

    Returns:
      original_build_logs (list[BuildLog]): A list of build logs.
    """
    if not document_id in self.original_build_logs:
      return []

    return self.original_build_logs[document_id]

  def get_all_original_building_logs(self) -> list[BuildLog]:
    """Get all the original build logs.

    The original build logs are used for the evaluation that calculates
    a loss of information score. Original refers to the build logs from before
    applying the node matcher.

    Returns:
      original_build_logs (list[BuildLog]): A list of build logs.
    """
    return list(itertools.chain(*self.original_build_logs.values()))

  def remove_node_by_id(self, id: UUID) -> None:
    """Remove a node by id.

    Also removes all the edges and properties that are related
    to this node.

    Args:
      id (UUID): The node's id.
    """
    if not id in self.nodes:
      raise NodeDoesNotExistException(
        f"Cannot delete a node that does not exist, id: {id}."
      )

    # Remove all the edges
    node_model: NodeModel = self.nodes[id]
    for edge_id in node_model["edges"]:
      # Remove the edge itself
      edge_model: EdgeModel = self.edges[edge_id]
      self._remove_edge(edge_model, edge_id, through_node=id)

    # Remove all the properties
    for prop_id in node_model["properties"]:
      self._remove_property(id=prop_id, property_model=self.properties[prop_id])

    # Update impacted child nodes
    for child_node_id in node_model["child_nodes"]:
      child_node_model: NodeModel = self.nodes[child_node_id]
      child_node_model["community"] = None

    # Update impacted community node (if it is has one)
    if community_id := node_model["community"]:
      community_node_model: NodeModel = self.nodes[community_id]
      community_node_model["child_nodes"].remove(id)

    # Update the doc_node_name_index
    for doc_id in {md["document_id"] for md in node_model["metadata"]}:
      del self.doc_node_name_index[doc_id][node_model["name"]]

    del self.nodes[id]
    self.change_log.append(
      ChangeLog(id=id, action=Action.DELETE, type=Node, level=node_model["level"])
    )

  def remove_document_by_id(self, id: UUID) -> None:
    """Remove a document by id.

    We only delete a node completely if it fully comes
    from a single document. If it has also been extracted from
    another document, then all of its attributes are considered
    under the same logic.

    Args:
      id (UUID): The document's id.
    """
    if not id in self.documents:
      raise DocumentDoesNotExistException(
        f"The document cannot be deleted as it does not exist, id: {id}"
      )

    # Select all nodes that are impacted (= all attributes must be checked)
    doc_nodes: list[tuple[UUID, NodeModel]] = [
      (node_id, self.nodes[node_id])
      for node_id in self.doc_node_name_index[id].values()
    ]
    nodes_to_check: list[tuple[UUID, NodeModel]] = []

    for node_id, node_model in doc_nodes:
      if {id} == {md["document_id"] for md in node_model["metadata"]}:
        self.remove_node_by_id(node_id)
      else:
        nodes_to_check.append((node_id, node_model))

    # Check all the properties / edges of the node to see if they need to be deleted
    # Same logic for deletion applies as to the node

    for node_id, node_model in nodes_to_check:
      # Check all the properties
      props_to_delete: list[UUID] = []
      for prop_id in node_model["properties"]:
        prop_model: PropertyModel = self.properties[prop_id]
        if {id} == {md["document_id"] for md in prop_model["metadata"]}:
          props_to_delete.append(prop_id)
          self._remove_property(id=prop_id, property_model=self.properties[prop_id])

      # Remove the properties from the node
      for prop_id in props_to_delete:
        node_model["properties"].remove(prop_id)

      # Check all the edges
      edges_to_delete: list[UUID] = []
      for edge_id in node_model["edges"]:
        edge_model: EdgeModel = self.edges[edge_id]
        if {id} == {md["document_id"] for md in edge_model["metadata"]}:
          edges_to_delete.append(edge_id)
          self._remove_edge(edge_model, edge_id, through_node=node_id)

      # Remove the edges from the node
      for edge_id in edges_to_delete:
        node_model["edges"].remove(edge_id)

    # Remove the document and update the doc node name index
    del self.documents[id]
    del self.doc_node_name_index[id]

  def _remove_edge(
    self, edge_model: EdgeModel, edge_id: UUID, through_node: UUID
  ) -> None:
    """Remove an edge from the repository.

    This method removes the edge from the stored edges and also
    removes the edge from both its nodes.

    Args:
      edge_model (EdgeModel): The edge's model as stored in the repository.
      edge_id (UUID): The edge's id.
      through_node (UUID): The id of the node through which this edge is being deleted.
    """
    del self.edges[edge_id]

    # Remove the edge from the other node's edges
    for impacted_node_id in {edge_model["frm"], edge_model["to"]}:
      if impacted_node_id == through_node:
        continue
      self.nodes[impacted_node_id]["edges"].remove(edge_id)

      # Log the deletion of an edge as a change log on both nodes
      self.change_log.append(
        ChangeLog(
          id=impacted_node_id,
          action=Action.UPDATE,
          type=Node,
          level=self.nodes[impacted_node_id]["level"],
          attributes=["edges"],
        )
      )

    self.change_log.append(
      ChangeLog(
        id=edge_id,
        action=Action.DELETE,
        type=Edge,
        level=self.nodes[edge_model["frm"]]["level"],
      )
    )

  def _remove_property(self, id: UUID, property_model: PropertyModel) -> None:
    del self.properties[id]

    self.change_log.append(
      ChangeLog(
        id=id,
        action=Action.DELETE,
        type=Property,
        level=self.nodes[property_model["node"]]["level"],
      )
    )
