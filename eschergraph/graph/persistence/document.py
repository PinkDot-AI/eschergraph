from __future__ import annotations

from uuid import UUID

from attrs import define
from attrs import field


@define
class DocumentData:
  """The document data object."""

  id: UUID
  name: str
  chunk_num: int
  token_num: int
  loss_of_information: float | None = field(default=None)
  std_loss_of_information: float | None = field(default=None)
