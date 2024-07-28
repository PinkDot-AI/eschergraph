from __future__ import annotations

from uuid import UUID

from attrs import define


@define
class Metadata:
  """The metadata that is attached to a part of the graph."""

  document_id: UUID
  chunk_id: int

  def __hash__(self) -> int:
    """The hash method that hashes the id and the chunk and sums them."""
    return hash(self.document_id) + hash(self.chunk_id)
