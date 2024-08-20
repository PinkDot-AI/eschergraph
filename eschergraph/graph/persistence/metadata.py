from __future__ import annotations

from uuid import UUID

from attrs import define


@define(hash=True)
class Metadata:
  """The metadata that is attached to a part of the graph."""

  document_id: UUID
  chunk_id: int
