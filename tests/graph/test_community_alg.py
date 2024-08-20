from __future__ import annotations

from uuid import UUID

import igraph as ig

from eschergraph.graph.community_alg import _create_level_igraph
from eschergraph.graph.community_alg import get_leidenalg_communities
from tests.graph.help import create_simple_extracted_graph


def test_create_level_igraph() -> None:
  _, nodes, edges = create_simple_extracted_graph()

  igraph: ig.Graph = _create_level_igraph(nodes)

  assert {v["name"] for v in igraph.vs} == {node.id for node in nodes}
  assert len(list(igraph.es)) == len(edges)


def test_get_leidenalg_communities() -> None:
  _, nodes, _ = create_simple_extracted_graph()
  partitions: list[list[UUID]] = get_leidenalg_communities(nodes)

  assert {n.id for n in nodes} == {id for p in partitions for id in p}
  assert len(partitions) < len(nodes)
