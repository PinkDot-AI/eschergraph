from __future__ import annotations

from attrs import define
from attrs import field

from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository


@define
class Graph:
  """The EscherGraph graph class."""

  name: str
  repository: Repository = field(factory=get_default_repository)

  # TODO: a method to add a node
  # TODO: a method to add an edge
