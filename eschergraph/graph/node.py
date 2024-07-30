from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from attrs import define
from attrs import field
from attrs import fields_dict

from eschergraph.exceptions import DataLoadingException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.base import LoadState

# To prevent circular import errors
if TYPE_CHECKING:
  from eschergraph.graph.edge import Edge
  from eschergraph.graph.persistence import Repository
  from eschergraph.graph.persistence import Metadata

# TODO: add a factory method to return the default Repository


@define
class Node(EscherBase):
  """A node in the graph.

  A node can be an entity from the source text, or a community formed
  from a (sub)graph of extracted entities.
  """

  _name: Optional[str] = field(default=None, metadata={"group": LoadState.CORE})
  _description: Optional[str] = field(default=None, metadata={"group": LoadState.CORE})
  _level: Optional[int] = field(default=None, metadata={"group": LoadState.CORE})
  """The level at which the node occurs. Level 0 refers to directly extracted entities, and levels
  above that are aggregated communities."""
  _properties: Optional[list[str]] = field(
    default=None, metadata={"group": LoadState.CORE}
  )
  _edges: Optional[set[Edge]] = field(
    default=None, metadata={"group": LoadState.CONNECTED}
  )
  _community: Optional[Node] = field(default=None, metadata={"group": LoadState.FULL})
  _child_nodes: Optional[list[Node]] = field(
    default=None, metadata={"group": LoadState.FULL}
  )
  _report: Optional[list[dict[str, str]]] = field(
    default=None, metadata={"group": LoadState.FULL}
  )
  _loadstate: LoadState = field(default=LoadState.REFERENCE)
  """The attribute that keeps track of the loading state of a Node."""
  repository: Repository = field(kw_only=True)

  @property
  def name(self) -> str:
    """The getter for the node name.

    Returns:
      The node's name.
    """
    self._check_loadstate(attr_name="_name")

    if not self._name:
      raise DataLoadingException("Node name has not been loaded.")

    return self._name

  @property
  def description(self) -> str:
    """The getter for the node description.

    Returns:
      The node's description.
    """
    self._check_loadstate(attr_name="_description")

    if not self._description:
      raise DataLoadingException("Node description has not been loaded.")

    return self._description

  @property
  def level(self) -> int:
    """The getter for the node level.

    The level indicates how close the node is to extraction from the source text.
    Level 0 indicates that the node has been extracted from the source text.
    Level 1 would correspond to the direct community of this node and so on.

    Returns:
      The node's level.
    """
    self._check_loadstate(attr_name="_level")

    if not self._level:
      raise DataLoadingException("Node level has not been loaded.")

    return self._level

  @property
  def properties(self) -> list[str]:
    """The getter for the node properties.

    Returns:
      The node's properties.
    """
    self._check_loadstate(attr_name="_properties")

    if not isinstance(self._properties, list):
      raise DataLoadingException("Node properties have not been loaded.")

    return self._properties

  @property
  def edges(self) -> set[Edge]:
    """The getter for the node edges.

    Returns:
      The node's edges.
    """
    self._check_loadstate(attr_name="edges")

    if not isinstance(self._edges, set):
      raise DataLoadingException("Node edges have not been loaded.")

    return self._edges

  @property
  def community(self) -> Optional[Node]:
    """The getter for the node community.

    Returns:
      The node's community or None if the node is not in a community.
    """
    self._check_loadstate(attr_name="_community")

    # Different check as node cannot have a community (top-layer)
    if not self.loadstate == fields_dict(Node)["_community"].metadata["group"]:
      raise DataLoadingException("The node community has not been loaded.")

    return self._community

  @property
  def child_nodes(self) -> list[Node]:
    """The getter for the child nodes.

    Returns:
      The node's children.
    """
    self._check_loadstate(attr_name="_child_nodes")

    if not isinstance(self._child_nodes, list):
      raise DataLoadingException("The child nodes have not been loaded.")

    return self._child_nodes

  @property
  def report(self) -> list[dict[str, str]]:
    """The getter for the node report.

    Returns:
      The node's report.
    """
    self._check_loadstate(attr_name="_report")

    if not isinstance(self._report, list):
      raise DataLoadingException("The node report has not been loaded.")

    return self._report

  @property
  def metadata(self) -> set[Metadata]:
    """The getter for the node metadata.

    Returns:
      The node's metadata.
    """
    self._check_loadstate(attr_name="_metadata")

    if not isinstance(self._metadata, set):
      raise DataLoadingException("The node metadata has not been loaded.")

    return self._metadata

  @property
  def loadstate(self) -> LoadState:
    """The getter for the loadstate of the node.

    Returns:
      The node's loadstate.
    """
    return self._loadstate

  @loadstate.setter
  def loadstate(self, loadstate: LoadState) -> None:
    """The setter for the loadstate of the node.

    We use a custom setter because we need to make sure that the value of the loadstate
    reflects that attributes that are loaded. In addition, the loadstate cannot yet decrease
    as we are not yet removing attributes on a class.

    Args:
      loadstate (LoadState): The loadstate to set and the state in which the node should
      be loaded.
    """
    # Do nothing if this decreases the loadstate
    if loadstate.value <= self._loadstate.value:
      return

    self.repository.load(self, loadstate=loadstate)
    self._loadstate = loadstate

  def _check_loadstate(self, attr_name: str) -> None:
    required_loadstate: LoadState = fields_dict(Node)[attr_name].metadata["group"]

    # Load more instance data from the repository if load state is too small
    if self.loadstate.value < required_loadstate.value:
      self.repository.load(self, loadstate=required_loadstate)
      self._loadstate = required_loadstate

  @classmethod
  def create_node(
    cls,
    name: str,
    description: str,
    level: int,
    repository: Repository,
    properties: Optional[list[str]] = None,
  ) -> Node:
    """The method that allows for the creation of a new node.

    When created, the load state is considered to be full and all attributes
    are set to their defaults.

    Args:
      name (str): The name of the node.
      description (str): The node description.
      level (int): The level of the node.
      repository (Repository): The repository that will store the node.
      properties (Optional[list[str]]): The optional properties for the node.

    Returns:
      The node that has been created.
    """
    return cls(
      name=name,
      description=description,
      level=level,
      properties=properties if properties else [],
      repository=repository,
      edges=set(),
      child_nodes=[],
      report=[],
      loadstate=LoadState.FULL,
    )
