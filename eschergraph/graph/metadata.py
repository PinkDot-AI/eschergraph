from __future__ import annotations

from attrs import define


@define
class Metadata:
  """The metadata that is attached to a part of the graph."""

  document_id: int
  chunk_id: int
