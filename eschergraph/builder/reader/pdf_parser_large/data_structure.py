from __future__ import annotations

from typing import Optional
from typing import TypedDict


# Define Pydantic models for Table and Figure


class BoundingRegion(TypedDict):
  """Represents a region on a page, defined by its page number and an optional polygon."""

  page_number: int
  polygon: Optional[list[float]]


class TableCell(TypedDict):
  """Defines a cell in a table, including its row/column indices, content, and bounding regions."""

  row_index: int
  column_index: int
  content: str
  bounding_regions: list[BoundingRegion]


class Paragraph(TypedDict):
  """Represents a paragraph with an optional role and associated content."""

  id: int
  role: str | None
  content: str


class Table(TypedDict):
  """Represents a table, including its structure (rows/columns), bounding regions, cells, caption, and page number."""

  id: int
  row_count: int
  column_count: int
  bounding_regions: list[BoundingRegion]
  cells: list[TableCell]
  caption: str | None
  page_num: int


class Figure(TypedDict):
  """Defines a figure with its content, caption, and associated page number."""

  id: str
  caption: str | None
  content: bytes
  page_num: int


class AnalysisResult(TypedDict):
  """Represents the result of an analysis, containing tables, figures, and paragraphs."""

  tables: list[Table]
  figures: list[Figure]
  paragraphs: list[Paragraph]
