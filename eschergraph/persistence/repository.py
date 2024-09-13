from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from eschergraph.graph.loading import LoadState

# Prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.base import EscherBase
  from eschergraph.graph import Node
  from eschergraph.graph import Edge
  from eschergraph.graph import Property
  from eschergraph.persistence.change_log import ChangeLog
  from eschergraph.persistence.document import Document


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

  @abstractmethod
  def get_change_log(self) -> list[ChangeLog]:
    """Get the list of change logs.

    The logs contain all the add operations that are performed for
    EscherBase objects. These can be used to sync other systems such as
    the vector database.

    Returns:
      A list of all changelogs.
    """
    raise NotImplementedError

  @abstractmethod
  def clear_change_log(self) -> None:
    """Clear all change logs.

    Use with caution. Should only be performed after syncing to external
    systems such as a vector database.
    """
    raise NotImplementedError

  @abstractmethod
  def remove_node_by_id(self, id: UUID) -> None:
    """Remove a node by id.

    Also removes all the edges and properties that are related
    to this node.

    Args:
      id (UUID): The node's id.
    """
    raise NotImplementedError

  @abstractmethod
  def remove_document_by_id(self, id: UUID) -> None:
    """Remove a document by id.

    Args:
      id (UUID): The document's id.
    """
    raise NotImplementedError

  @abstractmethod
  def add_document(self, document: Document) -> None:
    """Adds a document to the system.

    A document that already exists will be overwritten.

    Args:
      document (Document): The document data that needs to be added.
    """
    raise NotImplementedError

  @abstractmethod
  def get_document_by_id(self, id: UUID) -> Optional[Document]:
    """Retrieves documents based on a list of document UUIDs.

    Args:
      id (UUID): The UUID for the document to be fetched.

    Returns:
      Optional[Document]: Returns the Document or none if it does not exist.
    """
    raise NotImplementedError

  @abstractmethod
  def get_all_documents(self) -> list[Document]:
    """Get all documents that exist in a graph.

    Returns:
      list[Document]: A list containing all the documents.
    """
    raise NotImplementedError

  @abstractmethod
  def get_document_by_name(self, name: str) -> Optional[Document]:
    """Get a document by name.

    Args:
      name: str

    Returns:
      Optional[Document]: The document if a document with this name exists, and otherwise None.
    """
    raise NotImplementedError
