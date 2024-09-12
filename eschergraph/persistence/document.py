from __future__ import annotations

from uuid import UUID

from attrs import define


@define
class Document:
  """The document data object."""

  id: UUID
  name: str
  chunk_num: int
  token_num: int
