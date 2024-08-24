from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import define
from attrs import field

from eschergraph.exceptions import NodeCreationException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.community import Community
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.property import Property
from eschergraph.graph.utils import loading_getter_setter

# To prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.edge import Edge
  from eschergraph.graph.persistence import Repository


@loading_getter_setter
@define
class Node(EscherBase):
  """A node in the graph.

  A node can be an entity from the source text, or a community formed
  from a (sub)graph of extracted entities.
  """

  _name: Optional[str] = field(default=None, metadata={"group": LoadState.CORE})
  _description: Optional[str] = field(default=None, metadata={"group": LoadState.CORE})
  _level: Optional[int] = field(default=None, metadata={"group": LoadState.CORE})
  """The level at which the node occurs. Level 0 refers to directly extracted entities, and levels
  above that are aggregated communities."""
  _properties: Optional[list[Property]] = field(
    default=None, metadata={"group": LoadState.CORE}
  )
  _edges: Optional[set[Edge]] = field(
    default=None, metadata={"group": LoadState.CONNECTED}
  )
  _community: Optional[Community] = field(
    default=None, metadata={"group": LoadState.FULL}
  )
  _child_nodes: Optional[list[Node]] = field(
    default=None, metadata={"group": LoadState.FULL}
  )

  # Type annotations for the dynamically added properties
  name: str = field(init=False)
  description: str = field(init=False)
  level: int = field(init=False)
  properties: list[Property] = field(init=False)
  edges: set[Edge] = field(init=False)
  community: Community = field(init=False)
  child_nodes: list[Node] = field(init=False)

  @classmethod
  def create(
    cls,
    name: str,
    description: str,
    level: int,
    repository: Repository,
    metadata: Optional[set[Metadata]] = None,
    child_nodes: Optional[list[Node]] = None,
  ) -> Node:
    """The method that allows for the creation of a new node.

    When created, the load state is considered to be full and all attributes
    are set to their defaults.

    Args:
      name (str): The name of the node.
      description (str): The node description.
      level (int): The level of the node.
      repository (Repository): The repository that will store the node.
      metadata (Optional[set[Metadata]]): The optional metadata for the node.
      child_nodes (Optional[list[UUID]]): The optional child nodes for the node

    Returns:
      The node that has been created.
    """
    # Check if a node with the same name exists within a certain document (only at level 0)
    if level == 0:
      if not metadata:
        raise NodeCreationException(
          "A node extracted at level 0 needs to contain metadata."
        )
      document_id: UUID = next(iter(metadata)).document_id
      node_same_name: Optional[Node] = repository.get_node_by_name(
        name=name, document_id=document_id
      )

      # If a node with the same name exists for this document
      if node_same_name:
        # TODO: add logic to merge the description
        node_same_name.metadata = node_same_name.metadata | metadata
        return node_same_name

    return cls(
      name=name,
      description=description,
      level=level,
      properties=[],
      metadata=metadata if metadata else set(),
      repository=repository,
      community=Community(),
      edges=set(),
      child_nodes=child_nodes if child_nodes else [],
      loadstate=LoadState.FULL,
    )

  def add_property(self, description: str, metadata: Metadata) -> None:
    """Add a property to a node.

    The property is also added the the list of a node's properties.
    At the end of the method the property is also persisted.

    Args:
      description (str): The property's description.
      metadata (Metadata): The property's metadata.
    """
    property: Property = Property.create(
      node=self, description=description, metadata={metadata}
    )

    self.repository.add(property)

  def __eq__(self, other: object) -> bool:
    """The equals method for a node.

    Two nodes are equal if all their core attributes match.

    Args:
      other (object): The object to compare the node to.

    Returns:
      True if equal and false otherwise.
    """
    if isinstance(other, Node):
      return (
        self.name == other.name
        and self.description == other.description
        and self.level == other.level
        and self.metadata == other.metadata
        and self.properties == other.properties
      )

    return False

  def __hash__(self) -> int:
    """The hash method for a node.

    Only the id is used as this characterizes a node.

    Returns:
      The integer hash value.
    """
    return hash(self.id)

  # TODO: properly implement this method
  # Done quickly to prevent infinite recursion
  def __repr__(self) -> str:
    """The representation method for a node.

    Needs to be implemented because otherwise infinite recursion can occur.

    Returns:
      The string representation of a node.
    """
    return f"Node Name: {self.name} Description:{self.description}"
