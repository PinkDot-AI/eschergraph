from __future__ import annotations

from attrs import define
from attrs import field

from eschergraph.graph.metadata import Metadata
from eschergraph.storage import persistence


@persistence
@define
class Node:
  """A node in the graph.

  A node can be an entity from the source text, or a community formed
  from a (sub)graph of extracted entities.
  """

  name: str
  description: str
  metadata: Metadata
  level: int
  """The level at which the node occurs. Level 0 refers to directly extracted entities, and levels
  above that are aggregated communities."""
  properties: list[str] = field(factory=list)
  child_nodes: list[Node] = field(factory=list)
  report: list[dict[str, str]] = field(factory=list)
