from __future__ import annotations

from enum import Enum
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID
from uuid import uuid4

from attrs import define
from attrs import field
from attrs import fields_dict

from eschergraph.exceptions import DataLoadingException

# To prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.persistence import Metadata
  from eschergraph.graph.persistence import Repository


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
  _loadstate: LoadState = field(default=LoadState.REFERENCE)
  """The attribute that keeps track of the loading state of a Node."""
  repository: Repository = field(kw_only=True)

  def _check_loadstate(self, attr_name: str) -> None:
    """Check if the attribute has been loaded by the current loadstate.

    If not enough has been loaded, then load more instance data from the repository.

    Args:
      attr_name (str): The name of the attribute that starts with an underscore.
    """
    required_loadstate: LoadState = fields_dict(self.__class__)[attr_name].metadata[
      "group"
    ]

    # Load more instance data from the repository if load state is too small
    if self.loadstate.value < required_loadstate.value:
      self.repository.load(self, loadstate=required_loadstate)
      self._loadstate = required_loadstate

  @property
  def metadata(self) -> set[Metadata]:
    """The getter for the EscherGraph object metadata.

    Returns:
      The object's metadata.
    """
    self._check_loadstate(attr_name="_metadata")

    if not isinstance(self._metadata, set):
      raise DataLoadingException("The metadata has not been loaded.")

    return self._metadata

  @property
  def loadstate(self) -> LoadState:
    """The getter for the loadstate of an EscherGraph object.

    Returns:
      The object' loadstate.
    object's loadstate.
    """
    return self._loadstate

  @loadstate.setter
  def loadstate(self, loadstate: LoadState) -> None:
    """The setter for the loadstate of the EscherGraph base object.

    We use a custom setter because we need to make sure that the value of the loadstate
    reflects that attributes that are loaded. In addition, the loadstate cannot yet decrease
    as we are not yet removing attributes on a class.

    Args:
      loadstate (LoadState): The loadstate to set and the state in which the object should
      be loaded.
    """
    # Do nothing if this decreases the loadstate
    if loadstate.value <= self._loadstate.value:
      return

    self.repository.load(self, loadstate=loadstate)
    self._loadstate = loadstate
