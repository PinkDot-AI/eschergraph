from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import define

# Prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.builder.reader.multi_modal.data_structure import (
    VisualDocumentElement,
  )
  from eschergraph.persistence.document import Document


@define
class Chunk:
  """The chunk object."""

  text: str
  chunk_id: int
  doc_id: UUID
  page_num: Optional[int]


@define
class ProcessedFile:
  """A file processed by the reader."""

  document: Document
  full_text: str
  chunks: list[Chunk]
  visual_elements: Optional[list[VisualDocumentElement]] = None
