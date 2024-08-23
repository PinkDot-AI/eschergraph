from __future__ import annotations

from typing import Optional

from attrs import define
from attrs import field

from eschergraph.exceptions import NodeDoesNotExistException
from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository
from eschergraph.graph.property import Property


@define
class Graph:
  """The EscherGraph graph class."""

  name: str
  repository: Repository = field(factory=get_default_repository)

  def add_node(
    self,
    name: str,
    description: str,
    level: int,
    metadata: Metadata,
    properties: Optional[list[Property]] = None,
  ) -> Node:
    """Add a node to the graph.

    After creation, the node is persisted immediately to the repository.
    This is done as no data is saved in the graph object itself.

    Args:
      name (str): The name of the node.
      description (str): A description of the node.
      level (int): The level of the node.
      metadata (Metadata): The metadata of the node.
      properties (Optional[list[str]]): The optional properties of the node.

    Returns:
      The node that has been created.
    """
    node: Node = Node.create(
      name=name,
      description=description,
      level=level,
      repository=self.repository,
      properties=properties,
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
    if not frm or not to:
      raise NodeDoesNotExistException(
        "The node you are trying to add to an edge does not exist."
      )
    edge: Edge = Edge.create(
      frm=frm,
      to=to,
      description=description,
      repository=self.repository,
      metadata={metadata},
    )

    # Persist the edge
    self.repository.add(edge)

    return edge
