from __future__ import annotations

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.visualization.community import visualize_community_graph


def test_visualize_community_graph(
  community_graph: tuple[list[list[Node]], list[Edge]],
) -> None:
  visualize_community_graph(comms=community_graph[0], edges=community_graph[1])
