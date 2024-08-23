from __future__ import annotations

import json
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from attrs import asdict
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

  title: Optional[str] = field(default=None)
  summary: Optional[str] = field(default=None)
  findings: Optional[List[Finding]] = field(default=None)

  def __attrs_post_init__(self) -> None:
    """Either all are initialized or none are."""
    values = asdict(self).values()

    if all(value is None for value in values):
      return
    elif any(value is None for value in values):
      raise ValueError("Some properties were not initialized")

  def findings_to_json(self) -> str:
    """Convert the list of findings to a json output.

    Returns:
        str: Findings as a json formatted string
    """
    if self.findings is None:
      raise ValueError("Findings not found")
    return json.dumps([asdict(fnd) for fnd in self.findings], indent=4)


@define
class Finding:
  """A finding from a community creation."""

  summary: str
  explanation: str
