from __future__ import annotations

from typing import Any
from uuid import UUID

import igraph as ig
import leidenalg

from eschergraph.graph.node import Node


def _create_level_igraph(nodes: list[Node]) -> ig.Graph:
  node_ids: set[UUID] = {node.id for node in nodes}
  vertices: list[dict[str, UUID]] = [{"name": id} for id in node_ids]
  edges: list[dict[str, UUID | int]] = [
    {
      "source": edge.frm.id,
      "target": edge.to.id,
      "edge_weight": 1,  # All edges have equal weight
    }
    for node in nodes
    for edge in node.edges
    if edge.frm.id == node.id and edge.to.id in node_ids
  ]
  return ig.Graph.DictList(vertices=vertices, edges=edges, directed=True)


def get_leidenalg_communities(nodes: list[Node]) -> list[list[UUID]]:
  """Get the communities with the Leiden algorithm.

  The communities are calculated only for the provided nodes.

  Args:
    nodes (list[Node]): A list of nodes

  Returns:
    A list of lists, where each list corresponds to a community.
    Henceforth, each community is a list of node id's.
  """
  igraph: ig.Graph = _create_level_igraph(nodes)
  partition: Any = leidenalg.find_partition(igraph, leidenalg.ModularityVertexPartition)

  return [
    [node["name"] for node in subgraph.to_dict_list()[0]]
    for subgraph in partition.subgraphs()
  ]
