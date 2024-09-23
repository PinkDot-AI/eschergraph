from __future__ import annotations

from typing import Optional
from uuid import UUID

from attrs import define
from attrs import field


@define
class MetadataVisual:
  """The metadata that is attached to a part of the graph."""

  id: UUID
  content: str
  save_location: str
  page_num: int | None
  type: str

  def __hash__(self) -> int:
    """This is the hash function for the MetadataVisual datastructure."""
    return hash(self.id)


@define
class Metadata:
  """The metadata that is attached to a part of the graph."""

  document_id: UUID
  chunk_id: Optional[int]
  visual_metadata: Optional[MetadataVisual] = field(default=None)

  def __hash__(self) -> int:
    """This is the hash function for the Metadata datastructure."""
    visual_id: int | UUID = 1
    if isinstance(self.visual_metadata, dict):
      self.visual_metadata = MetadataVisual(**self.visual_metadata)
    if self.visual_metadata:
      visual_id = self.visual_metadata.id

    return hash((self.document_id, self.chunk_id, visual_id))
