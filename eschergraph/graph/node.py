from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import define
from attrs import field

from eschergraph.exceptions import NodeCreationException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.community import Community
from eschergraph.graph.community import Report
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence import Metadata
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
  _properties: Optional[list[str]] = field(
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
  _report: Optional[Report] = field(default=None, metadata={"group": LoadState.FULL})

  # Type annotations for the dynamically added properties
  name: str = field(init=False)
  description: str = field(init=False)
  level: int = field(init=False)
  properties: list[str] = field(init=False)
  edges: set[Edge] = field(init=False)
  community: Community = field(init=False)
  child_nodes: list[Node] = field(init=False)
  report: Report = field(init=False)

  @classmethod
  def create(
    cls,
    name: str,
    description: str,
    level: int,
    repository: Repository,
    properties: Optional[list[str]] = None,
    metadata: Optional[set[Metadata]] = None,
  ) -> Node:
    """The method that allows for the creation of a new node.

    When created, the load state is considered to be full and all attributes
    are set to their defaults.

    Args:
      name (str): The name of the node.
      description (str): The node description.
      level (int): The level of the node.
      repository (Repository): The repository that will store the node.
      properties (Optional[list[str]]): The optional properties for the node.
      metadata (Optional[set[Metadata]]): The optional metadata for the node.

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
      properties=properties if properties else [],
      metadata=metadata if metadata else set(),
      repository=repository,
      community=Community(),
      edges=set(),
      child_nodes=[],
      report=Report(),
      loadstate=LoadState.FULL,
    )

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
