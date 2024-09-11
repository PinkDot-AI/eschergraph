from __future__ import annotations

from typing import Optional
from typing import TypedDict


# Define Pydantic models for Table and Figure
class BoundingRegion(TypedDict):
  page_number: int
  polygon: Optional[list[float]]


class TableCell(TypedDict):
  row_index: int
  column_index: int
  content: str
  bounding_regions: list[BoundingRegion]


class Paragraph(TypedDict):
  id: int
  role: str | None
  content: str


class Table(TypedDict):
  id: int
  row_count: int
  column_count: int
  bounding_regions: list[BoundingRegion]
  cells: list[TableCell]


class Figure(TypedDict):
  id: str
  content: bytes


class AnalysisResult(TypedDict):
  tables: list[Table]
  figures: list[Figure]
  paragraphs: list[Paragraph]
