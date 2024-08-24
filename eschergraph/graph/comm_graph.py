from __future__ import annotations

from uuid import UUID

from attrs import define


@define
class CommunityGraphResult:
  """The community graph result data structure.

  This community graph is returned after applying
  the Leiden algorithm, for example.
  """

  partitions: list[list[UUID]]
  """A list of lists, where each each inner list
  is a community containing the respective node id's"""
  edges: list[UUID]
  """A list of edge id's for all the edges in the community graph."""
