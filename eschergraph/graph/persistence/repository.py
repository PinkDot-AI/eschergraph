from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from eschergraph.graph.base import LoadState
from eschergraph.graph.node import Node


class NodeRepository(ABC):
  """An abstract base class for a a node repository."""

  @abstractmethod
  def load(self, node: Node, loadstate: LoadState = LoadState.CORE) -> Node:
    """Load the attributes of a node that belong to the specified loading state.

    Args:
      node (Node): The node for which the attributes need to be loaded.
      loadstate (LoadState): The state that needs to be loaded. The default
        is CORE.

    Returns:
      The specified node with the attributes from the load state loaded.

    """
    raise NotImplementedError

  @abstractmethod
  def save(self, node: Node) -> None:
    """Save (persist) the node to the data storage.

    Args:
      node (Node): The node to save.
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
