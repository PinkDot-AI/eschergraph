from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.utils import loading_getter_setter

# Prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.node import Node


@loading_getter_setter
@define
class Property(EscherBase):
  """The property class.

  Conceptually, we consider a property to be the same as en edge.
  Therefore, a property can be considered as sort of an edge between the
  node and itself.
  """

  node: Node = field(kw_only=True)
  _description: Optional[str] = field(default=None, metadata={"group": LoadState.CORE})

  # The type annotation for the properties added by the decorator
  description: str = field(init=False)

  @classmethod
  def create(
    cls,
    node: Node,
    description: str,
    metadata: Optional[set[Metadata]] = None,
  ) -> Property:
    """Create a new property.

    The property that is created is automatically added to the specified node.

    Args:
      node (Node): The node to which the property belongs.
      description (str): The property's description.
      metadata (Optional[set[Metadata]]): The optional set with metadata about the property's extraction.


    Returns:
      The newly created property.
    """
    # The same repository as the node
    property: Property = cls(
      node=node,
      description=description,
      repository=node.repository,
      metadata=metadata if metadata else set(),
      loadstate=LoadState.FULL,
    )

    # Add the property to the node
    node.properties.append(property)

    return property

  def __eq__(self, other: object) -> bool:
    """The equals method for a property.

    Two property objects are considered equal if they have the same description, and
    if they belong to the same node.

    Args:
      other (object): The object to compare the property to.

    Returns:
      True if equal and False otherwise.
    """
    if isinstance(other, Property):
      return self.description == other.description and self.node.id == other.node.id
    return False

  def __hash__(self) -> int:
    """The hash function for a property.

    The hash is computed based on the id as this uniquely defines the property.

    Returns:
      The computed hash value, which is an integer.
    """
    return hash(self.id)
