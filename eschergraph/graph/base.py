from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID
from uuid import uuid4

from attrs import define
from attrs import field

# To prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.persistence import Metadata


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
class EscherBase(ABC):
  """The base class for objects in the package that need to be persisted."""

  id: UUID = field(factory=uuid4, metadata={"group": LoadState.REFERENCE})
  _metadata: Optional[set[Metadata]] = field(
    default=None, hash=False, metadata={"group": LoadState.CORE}
  )

  @abstractmethod
  def _check_loadstate(self, attr_name: str) -> None:
    """Check if the attribute has been loaded by the current loadstate.

    If not enough has been loaded, then load more instance data from the repository.

    Args:
      attr_name (str): The name of the attribute that starts with an underscore.
    """
    raise NotImplementedError
