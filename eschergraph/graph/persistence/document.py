from __future__ import annotations

from uuid import UUID

from attrs import define


@define
class DocumentData:
  """This is the document data object."""

  id: UUID
  name: str
  chunk_num: int
  token_num: int
  loss_of_information: float | None
  std_loss_of_information: float | None
