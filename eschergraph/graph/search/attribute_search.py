from __future__ import annotations

from attrs import define

from eschergraph.persistence import Metadata


@define
class AttributeSearch:
  """This is the dataclass for the attribute search object."""

  text: str
  metadata: set[Metadata] | None
  parent_nodes: list[str]
