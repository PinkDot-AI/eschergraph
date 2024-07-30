from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from eschergraph.graph.base import EscherBase
from eschergraph.graph.base import LoadState
from eschergraph.graph.node import Node


# Potentially change the EscherBase type hint to Node | Edge for readability!
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
  def save(self, object: EscherBase) -> None:
    """Save (persist) the EscherGraph object to the data storage.

    Args:
      object (EscherBase): The object to save.
    """
    raise NotImplementedError

  @abstractmethod
  def get_node_by_name(self, name: str) -> Node:
    """Get a node by name.

    Args:
      name (str): The node to get.

    Returns:
      The node that matches the given name.
    """
    raise NotImplementedError
