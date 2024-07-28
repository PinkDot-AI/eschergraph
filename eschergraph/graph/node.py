from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

from eschergraph.graph.base import EscherBase

# To prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.edge import Edge


@define(hash=True)
class Node(EscherBase):
  """A node in the graph.

  A node can be an entity from the source text, or a community formed
  from a (sub)graph of extracted entities.
  """

  name: str = field(kw_only=True)
  description: str = field(kw_only=True)
  level: int = field(kw_only=True)
  """The level at which the node occurs. Level 0 refers to directly extracted entities, and levels
  above that are aggregated communities."""
  community: Optional[Node] = None
  properties: list[str] = field(factory=list, hash=False)
  child_nodes: list[Node] = field(factory=list, hash=False)
  edges: set[Edge] = field(factory=set, hash=False)
  report: list[dict[str, str]] = field(factory=list, hash=False)
