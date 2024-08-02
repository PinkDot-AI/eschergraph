from __future__ import annotations

from typing import Optional
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

if TYPE_CHECKING:
  from eschergraph.graph.node import Node


@define
class Community:
  """A community class that holds a node if the node is part of a community."""

  node: Optional[Node] = field(default=None)
