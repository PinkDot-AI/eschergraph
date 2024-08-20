from __future__ import annotations

from uuid import UUID

import igraph as ig

from eschergraph.graph.node import Node


def _create_level_igraph(nodes: list[Node]) -> ig.Graph:
  node_ids: set[UUID] = {node.id for node in nodes}
  vertices: list[dict[str, UUID]] = [{"name": id} for id in node_ids]
  edges: list[dict[str, UUID]] = [
    {
      "source": edge.frm.id,
      "target": edge.to.id,
    }
    for node in nodes
    for edge in node.edges
    if edge.frm.id == node.id and edge.to.id in node_ids
  ]
  return ig.Graph.DictList(vertices=vertices, edges=edges, directed=True)
