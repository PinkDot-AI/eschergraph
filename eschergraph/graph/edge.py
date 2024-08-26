from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

from eschergraph.exceptions import EdgeCreationException
from eschergraph.exceptions import RepositoryException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.utils import loading_getter_setter

# Prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.node import Node


@loading_getter_setter
@define
class Edge(EscherBase):
  """The edge in an EscherGraph.

  Although, we specify from and to nodes, edges are actually undirectional
  as they are richly descriptive. This is also reflected in the equals method.

  Note that the loadstate for an Edge is directly passed on to the two nodes that are
  connected by the edge.
  """

  frm: Node = field(kw_only=True)
  to: Node = field(kw_only=True)
  _description: Optional[str] = field(default=None, metadata={"group": LoadState.CORE})

  # The type annotation for the dynamically added property
  description: str = field(init=False)

  @classmethod
  def create(
    cls,
    frm: Node,
    to: Node,
    description: str,
    metadata: Optional[set[Metadata]] = None,
  ) -> Edge:
    """The method that allows for the creation of a new edge.

    Note that edges do have a to and from method, but they
    are undirectional. This is also reflected in the equals method.

    Args:
      frm (Node): The from node in the edge.
      to (Node): The to node in the edge.
      description (str): A rich description of the relation.
      metadata (Optional[set[Metadata]]): The optional metadata for the edge.

    Returns:
      A new edge.
    """
    if frm.id == to.id:
      raise EdgeCreationException(
        "An edge should be created between two different nodes."
      )

    if not frm.repository is to.repository:
      raise RepositoryException(
        "The two nodes that are connected by an edge need to have the same repository."
      )

    edge: Edge = cls(
      frm=frm,
      to=to,
      description=description,
      repository=frm.repository,
      metadata=metadata if metadata else set(),
      loadstate=LoadState.FULL,
    )

    # Add the edge to the nodes
    frm.edges.add(edge)
    to.edges.add(edge)

    return edge

  def __eq__(self, other: object) -> bool:
    """The equals method for an edge.

    Two edges are equal if they have the same description and run between the same nodes.

    Args:
      other (object): The object to compare the edge to.

    Returns:
      True if equal and false otherwise.
    """
    if isinstance(other, Edge):
      return {self.frm.id, self.to.id} == {
        other.frm.id,
        other.to.id,
      } and self.description == other.description

    return False

  def __hash__(self) -> int:
    """The hash function for an edge.

    Returns:
     The integer hash value for an edge.
    """
    return hash((self.id, self.frm.id, self.to.id, self.description))
