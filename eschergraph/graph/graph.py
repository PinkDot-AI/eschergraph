from __future__ import annotations

from typing import Any
from uuid import UUID

from attrs import define
from attrs import field

from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository
from eschergraph.graph.persistence.vector_db import get_vector_db
from eschergraph.graph.persistence.vector_db import VectorDB
from eschergraph.graph.property import Property


@define
class Graph:
  """The EscherGraph graph class."""

  name: str
  repository: Repository = field(factory=get_default_repository)
  vector_db: VectorDB = field(factory=get_vector_db)
  # embedding_model:Embedding =

  def __init__(self) -> None:
    """This is the initializer of the graph class for getting the vectordb."""
    self.vector_db = get_vector_db()

  def add_node(
    self,
    name: str,
    description: str,
    level: int,
    metadata: Metadata,
  ) -> Node:
    """Add a node to the graph.

    After creation, the node is persisted immediately to the repository.
    This is done as no data is saved in the graph object itself.

    Args:
      name (str): The name of the node.
      description (str): A description of the node.
      level (int): The level of the node.
      metadata (Metadata): The metadata of the node.

    Returns:
      The node that has been created.
    """
    node: Node = Node.create(
      name=name,
      description=description,
      level=level,
      repository=self.repository,
      metadata={metadata},
    )

    # Persist the node
    self.repository.add(node)

    return node

  def add_edge(self, frm: Node, to: Node, description: str, metadata: Metadata) -> Edge:
    """Add an edge to the graph.

    The edge is persisted to the repository straight away.

    Args:
      frm (Node): The from node in the edge.
      to (Node): The to node in the edge.
      description (str): A rich description of the relation.
      metadata (Metadata): The metadata of the edge.

    Returns:
      The edge that has been added to the graph.
    """
    edge: Edge = Edge.create(
      frm=frm,
      to=to,
      description=description,
      metadata={metadata},
    )

    # Persist the edge
    self.repository.add(edge)

    return edge

  def sync_vectordb(self, collection_name: str, level: int = 0) -> None:
    """Synchronizes the vector database with the latest changes in the repository.

    Args:
        collection_name (str): The name of the vector database collection where documents should be stored.
        level (int, optional): The hierarchical level at which the metadata is being synced. Default is 0.
    """
    docs: list[str] = []
    ids: list[UUID] = []
    metadata = list[dict[str, Any]]
    for log in self.repository.get_change_log():
      if isinstance(log.type, Node):
        if log.action == "delete" or log.action == "update":
          self.vector_db.delete_with_id([log.id], collection_name)
          if log.action == "delete":
            continue
        node: Node = self.repository.get_node_by_id(log.id)
        docs.append(node.name)
        metadata.append({
          "level": level,
          "type": "node",
          "entity_frm": "",
          "entity_to": "",
          "chunk_id": "",  # node.metadata.chunk_id, #node is currently a set of metadata but chroma cannot handle that...
          "document_id": "",  # node.metadata.document_id
        })
      elif isinstance(log.type, Edge):
        if log.action == "delete" or log.action == "update":
          self.vector_db.delete_with_id([log.id], collection_name)
          if log.action == "delete":
            continue
        edge: Edge = self.repository.get_edge_by_id(log.id)
        docs.append(edge.description)
        metadata.append({
          "level": level,
          "type": "edge",
          "entity_frm": edge.frm.name,
          "entity_to": edge.to.name,
          "chunk_id": "",  # edge.metadata.chunk_id,
          "document_id": "",  # edge.metadata.document_id
        })
      elif isinstance(log.type, Edge):
        if log.action == "delete" or log.action == "update":
          self.vector_db.delete_with_id([log.id], collection_name)
          if log.action == "delete":
            continue
        property: Property = self.repository.get_property_by_id(log.id)
        docs.append(property.description)
        metadata.append({
          "level": level,
          "type": "property",
          "entity_frm": property.node.name,
          "entity_to": "",
          "chunk_id": "",  # edge.metadata.chunk_id,
          "document_id": "",  # edge.metadata.document_id
        })
      ids.append(log.id)
