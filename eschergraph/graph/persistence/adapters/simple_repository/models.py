from __future__ import annotations

from typing import List
from typing import Optional
from typing import TypedDict
from uuid import UUID


class MetadataModel(TypedDict):
  """The persistent data model for an object's metadata."""

  document_id: UUID
  chunk_id: int


class FindingModel(TypedDict):
  """The persistent data model for a finding."""

  summary: str
  explanation: str


class ReportModel(TypedDict):
  """The persistent data model for a report."""

  title: Optional[str]
  summary: Optional[str]
  findings: Optional[List[FindingModel]]


class NodeModel(TypedDict):
  """The persistent data model for a node."""

  name: str
  description: str
  level: int
  properties: list[str]
  edges: set[UUID]
  community: Optional[UUID]
  report: ReportModel
  metadata: list[MetadataModel]
  child_nodes: set[UUID]


class EdgeModel(TypedDict):
  """The persistent data model for an edge."""

  frm: UUID
  to: UUID
  description: str
  metadata: list[MetadataModel]
