from __future__ import annotations

from attrs import define

from eschergraph.graph.persistence.metadata import Metadata


@define
class Property:
  """This is the dataclass for the properties."""

  description: str
  metadata: Metadata
