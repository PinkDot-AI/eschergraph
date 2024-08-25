from __future__ import annotations

from typing import Optional
from typing import TypedDict
from uuid import UUID


class MetadataModel(TypedDict):
  """The persistent data model for an object's metadata."""

  document_id: UUID
  chunk_id: int


class PropertyModel(TypedDict):
  """The persistent data model for a property."""

  description: str
  node: UUID
  metadata: list[MetadataModel]


class NodeModel(TypedDict):
  """The persistent data model for a node."""

  name: str
  description: str
  level: int
  properties: list[UUID]
  edges: set[UUID]
  community: Optional[UUID]
  metadata: list[MetadataModel]
  child_nodes: set[UUID]


class EdgeModel(TypedDict):
  """The persistent data model for an edge."""

  frm: UUID
  to: UUID
  description: str
  metadata: list[MetadataModel]
