from __future__ import annotations

from enum import Enum
from uuid import UUID

from attrs import define
from attrs import field

from eschergraph.graph.base import EscherBase


class Action(Enum):
  """The action that occurred to the EscherBase object."""

  CREATE: str = "create"
  UPDATE: str = "update"
  DELETE: str = "delete"


@define
class ChangeLog:
  """The log othat captures a persisted change to an EscherBase object."""

  id: UUID
  """The primary key of the object."""
  action: Action
  type: type[EscherBase]
  level: int
  """The level in the graph at which the change occurred."""
  attributes: list[str] = field(factory=list)
  """A list with the name of the attributes could be impacted."""
