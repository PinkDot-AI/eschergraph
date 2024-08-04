from __future__ import annotations

from attrs import define

from eschergraph.graph.persistence import Repository


@define
class Graph:
  """The EscherGraph graph class."""

  repository: Repository
  name: str
  save_location: str

  # TODO: a method to add a node
  # TODO: a method to add an edge
