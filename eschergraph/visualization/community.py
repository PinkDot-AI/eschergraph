from __future__ import annotations

import seaborn as sns

from eschergraph.graph import Node


def visualize_community(comms: list[list[Node]]) -> None:
  """Visualize a graph of communities.

  Given a list containing lists of nodes, where each
  list of nodes corresponds to a community.

  Args:
    comms (list[list[node]]): A list of communities.
  """
  ...


def _community_to_colors(comms: list[list[str]]) -> None:
  palette: list[str] = sns.color_palette("hls", len(comms)).as_hex()

  return
