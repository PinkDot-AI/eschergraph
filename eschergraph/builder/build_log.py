from __future__ import annotations

from typing import TypedDict

from attrs import define
from attrs import field

from eschergraph.graph.persistence import Metadata


class NodeExt(TypedDict):
  """A directly extracted node."""

  name: str
  description: str


class EdgeExt(TypedDict):
  """An directly extracted edge."""

  source: str
  target: str
  relationship: str


class PropertyExt(TypedDict):
  """A directly extracted property."""

  entity_name: str
  properties: list[str]


class NodeEdgeExt(TypedDict):
  """Nodes and edges as extracted and returned by LLM."""

  entities: list[NodeExt]
  relationships: list[EdgeExt]


@define
class BuildLog:
  """This is the dataclass for the building logs."""

  metadata: Metadata
  nodes: list[NodeExt]
  edges: list[EdgeExt]
  chunk_text: str
  properties: list[PropertyExt] = field(factory=list)
