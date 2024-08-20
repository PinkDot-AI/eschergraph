from __future__ import annotations

import igraph as ig

from eschergraph.graph.community_alg import _create_level_igraph
from tests.graph.help import create_simple_extracted_graph


def test_create_level_igraph() -> None:
  _, nodes, edges = create_simple_extracted_graph()

  igraph: ig.Graph = _create_level_igraph(nodes)

  assert {v["name"] for v in igraph.vs} == {node.id for node in nodes}
  assert len(list(igraph.es)) == len(edges)
