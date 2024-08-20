from __future__ import annotations

import json
from typing import List
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


@define
class Report:
  """A report of a community node."""

  title: str
  summary: str
  findings: List[Finding]

  def findings_to_json(self) -> str:
    """Convert the list of findings to a json output.

    Returns:
        str: Findings as a json formatted string
    """
    return json.dumps([fnd.to_json() for fnd in self.findings], indent=4)


@define
class Finding:
  """A finding from a community creation."""

  summary: str
  explanation: str

  def to_json(self) -> str:
    """Convert finding to json formatted string."""
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
