from __future__ import annotations

from enum import Enum


class LoadState(Enum):
  """The enum class that contains the load states for an EscherGraph object.

  The integer values indicate the loading hierarchy. A load state includes also
  all the states with a lower value.
  """

  REFERENCE = 0
  CORE = 1
  CONNECTED = 2
  FULL = 3
