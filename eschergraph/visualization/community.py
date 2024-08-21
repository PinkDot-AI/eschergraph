from __future__ import annotations

import seaborn as sns

from eschergraph.graph import Edge
from eschergraph.graph import Node


def visualize_community(comms: list[list[Node]], edges: list[Edge]) -> None:
  """Visualize a graph of communities.

  Communities are provided in a list containing lists of nodes, where each
  list of nodes corresponds to a community.

  Args:
    comms (list[list[node]]): A list of communities.
    edges (list[Edge]): The list of edges in the community graph.
  """
  ...


def _community_to_colors(comms: list[list[str]]) -> list[dict[str, str | int]]:
  palette: list[str] = sns.color_palette("hls", len(comms)).as_hex()
  colored_nodes: list[dict[str, str | int]] = []
  group: int = 0
  for comm in comms:
    color: str = palette.pop()
    group += 1
    for node in comm:
      colored_nodes.append({"node": node, "color": color, "group": group})
  return colored_nodes
