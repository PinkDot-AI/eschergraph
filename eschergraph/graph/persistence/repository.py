from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Optional
from typing import TYPE_CHECKING

from eschergraph.graph.loading import LoadState

if TYPE_CHECKING:
  from eschergraph.graph.base import EscherBase
  from eschergraph.graph.node import Node


class Repository(ABC):
  """An abstract base class for an EscherGraph repository."""

  @abstractmethod
  def load(self, object: EscherBase, loadstate: LoadState = LoadState.CORE) -> None:
    """Load the attributes of an EscherGraph object that belong to the specified loading state.

    The attributes are loaded on the specified object and nothing is returned.

    Args:
      object (EscherBase): The object for which the attributes need to be loaded.
      loadstate (LoadState): The state that needs to be loaded. The default
        is CORE.
    """
    raise NotImplementedError

  @abstractmethod
  def add(self, object: EscherBase) -> None:
    """Add (persist) the EscherGraph object to the data storage.

    If the object already exists then it will be updated by calling this method.

    Args:
      object (EscherBase): The object to save.
    """
    raise NotImplementedError

  @abstractmethod
  def get_node_by_name(
    self, name: str, loadstate: LoadState = LoadState.CORE, level: Optional[int] = None
  ) -> Optional[Node]:
    """Get a node by name at a certain level.

    Returns the node, and None if no node is found.

    Args:
      name (str): The node to get.
      loadstate (LoadState): The state in which the node should be loaded.
      level (Optional[int]): The level at which the node exists. The default is 0.

    Returns:
      The node that matches the name at the specified level.
    """
    raise NotImplementedError

  @abstractmethod
  def save(self) -> None:
    """Explicitly indicate that the repository should save the graph to its persistent storage.

    This method might not be necessary for running databases but can be useful
    in some cases. Essentially, it amounts to comitting the changes.
    """
    raise NotImplementedError
