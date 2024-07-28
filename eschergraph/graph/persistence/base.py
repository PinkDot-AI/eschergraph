from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from attrs import define
from attrs import field


# TODO: add a hash method for checking if an object should be updated / refreshed
@define
class EscherBase:
  """The base class for objects in the package that need to be persisted."""

  id: UUID = field(factory=uuid4)
  persisted: bool = field(default=False)
  loaded: bool = field(default=True)
