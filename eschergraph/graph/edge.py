from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState
from eschergraph.graph.utils import loading_getter_setter

# Prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.node import Node


@loading_getter_setter
@define(hash=True)
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

  def __eq__(self, other: object) -> bool:
    """The equals method for two nodes.

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
