from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID
from uuid import uuid4

from attrs import define
from attrs import field

from eschergraph.graph.persistence.metadata import Metadata


class LoadState(Enum):
  """The enum class that contains the load states for an Eschergraph object.

  The integer values indicate the loading hierarchy. A load state includes also
  all the states with a lower value.
  """

  REFERENCE = 0
  CORE = 1
  CONNECTED = 2
  FULL = 3


@define
class EscherBase:
  """The base class for objects in the package that need to be persisted."""

  id: UUID = field(factory=uuid4, metadata={"group": LoadState.REFERENCE})
  _metadata: Optional[set[Metadata]] = field(
    default=None, hash=False, metadata={"group": LoadState.CORE}
  )
