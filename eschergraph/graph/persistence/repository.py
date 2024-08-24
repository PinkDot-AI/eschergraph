from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from eschergraph.graph.loading import LoadState

if TYPE_CHECKING:
  from eschergraph.graph.base import EscherBase
  from eschergraph.graph.node import Node
  from eschergraph.graph.edge import Edge
  from eschergraph.graph.property import Property


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
    self, name: str, document_id: UUID, loadstate: LoadState = LoadState.CORE
  ) -> Optional[Node]:
    """Get a node from a certain document by name.

    Returns the node, and None if no node is found.
    The nodes that are returned from this method are all at level 0.

    Args:
      name (str): The node to get.
      document_id (UUID): The id of the document from which the node has been extracted.
      loadstate (LoadState): The state in which the node should be loaded.

    Returns:
      The node that matches the name in the specified document.
    """
    raise NotImplementedError

  @abstractmethod
  def get_max_level(self) -> int:
    """Get the highest non-root level of the graph.

    Returns:
        int: The highest level
    """
    raise NotImplementedError

  @abstractmethod
  def save(self) -> None:
    """Explicitly indicate that the repository should save the graph to its persistent storage.

    This method might not be necessary for running databases but can be useful
    in some cases. Essentially, it amounts to comitting the changes.
    """
    raise NotImplementedError

  @abstractmethod
  def get_node_by_id(self, id: UUID) -> Optional[Node]:
    """Get a node by id.

    If a node with this id is not found, then None is returned.

    Args:
      id (UUID): The node's id.

    Returns:
      The node or None if no node with this id exists.
    """
    raise NotImplementedError

  @abstractmethod
  def get_edge_by_id(self, id: UUID) -> Optional[Edge]:
    """Get an edge by id.

    If no edge with this id is found, then None is returned.

    Args:
      id (UUID): The edge's id.

    Returns:
      The edge or None if no edge is found.
    """
    raise NotImplementedError

  @abstractmethod
  def get_property_by_id(self, id: UUID) -> Optional[Property]:
    """Get a property by id.

    If no property with this id is found, then None is returned.

    Args:
      id (UUID): The property's id.

    Returns:
      The property of None if no property is found.
    """
    raise NotImplementedError

  @abstractmethod
  def get_all_at_level(self, level: int) -> list[Node]:
    """Get all nodes at a certain level.

    Note that level 0 corresponds to nodes that are directly extracted
    from a source text. Level 1 corresponds to the direct communities of these nodes.
    And so on.

    Args:
      level (int): The level at which the nodes should occur.

    Returns:
      A list with all the nodes at the specified level.
    """
    raise NotImplementedError
