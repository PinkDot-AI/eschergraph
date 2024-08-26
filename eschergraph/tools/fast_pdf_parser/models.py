from __future__ import annotations

from typing import TypedDict


class PdfParsedSegment(TypedDict):
  """A parsed PDF segment."""

  left: float
  top: float
  width: float
  height: float
  page_number: int
  page_width: int
  page_height: int
  text: str
  type: str
