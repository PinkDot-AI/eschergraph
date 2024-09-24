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

  def __hash__(self) -> int:
    """The hash method for a document.

    Method is written for testing, but can also be used elsewhere.

    Returns:
      int: The document's hash.
    """
    return hash((self.id, self.name, self.chunk_num, self.token_num))
