from __future__ import annotations

from typing import Optional
from typing import TypedDict
from uuid import UUID

from eschergraph.graph.community import Report

from eschergraph.graph.property import Property


class MetadataModel(TypedDict):
  """The persistent data model for an object's metadata."""

  document_id: UUID
  chunk_id: int


class NodeModel(TypedDict):
  """The persistent data model for a node."""

  name: str
  description: str
  level: int
  properties: list[Property]
  edges: set[UUID]
  community: Optional[UUID]
  report: Report
  metadata: list[MetadataModel]
  child_nodes: set[UUID]


class EdgeModel(TypedDict):
  """The persistent data model for an edge."""

  frm: UUID
  to: UUID
  description: str
  metadata: list[MetadataModel]
