from __future__ import annotations

from typing import Optional
from typing import TypedDict
from uuid import UUID


class MetadataModel(TypedDict):
  """The persistent data model for an object's metadata."""

  document_id: UUID
  chunk_id: int


class NodeModel(TypedDict):
  """The persistent data model for a node."""

  name: str
  description: str
  level: int
  properties: list[str]
  edges: set[EdgeModel]
  community: Optional[UUID]
  report: list[dict[str, str]]
  metadata: set[MetadataModel]


class EdgeModel(TypedDict):
  """The persistent data model for an edge."""

  id: UUID
  frm: UUID
  to: UUID
  description: str
  metadata: set[MetadataModel]