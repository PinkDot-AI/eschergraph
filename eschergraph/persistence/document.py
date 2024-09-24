from __future__ import annotations

from typing import Any
from uuid import UUID

from attrs import define
from attrs import field


@define
class Document:
  """The document data object."""

  id: UUID
  name: str
  chunk_num: int
  token_num: int
  tags: dict[str, Any] = field(factory=dict)
  """"The (semi-)structured metadata that can be used for filtering."""
