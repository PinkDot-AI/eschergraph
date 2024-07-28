from __future__ import annotations

from typing import Optional

from attrs import define
from attrs import field

from eschergraph.graph.metadata import Metadata
from eschergraph.graph.persistence import EscherBase


@define
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
  metadata: set[Metadata] = field(factory=set)
  properties: list[str] = field(factory=list)
  child_nodes: list[Node] = field(factory=list)
  report: list[dict[str, str]] = field(factory=list)
