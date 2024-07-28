from __future__ import annotations

from attrs import define
from attrs import field

from eschergraph.graph.base import EscherBase
from eschergraph.graph.node import Node


@define(hash=True)
class Edge(EscherBase):
  """The edge in an EscherGraph.

  Although, we specify from and to nodes. Edges are actually undirectional
  as they are richly descriptive. This is also reflected in the equals method.
  """

  frm: Node = field(kw_only=True)
  to: Node = field(kw_only=True)
  description: str = field(kw_only=True)

  def __eq__(self, other: object) -> bool:
    """The equals method for two nodes.

    Two edges are equal if they have the same description and run between the same nodes.

    Args:
      other (object): The object to compare the edge to.

    Returns:
      True if equal and false otherwise.
    """
    if isinstance(other, Edge):
      return {self.frm, self.to} == {
        other.frm,
        other.to,
      } and self.description == other.description

    return False
