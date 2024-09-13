from __future__ import annotations

from uuid import UUID

from attrs import define


@define
class VectorSearchResult:
  """The result from a vector search."""

  id: UUID
  chunk: str
  type: str
  distance: float
