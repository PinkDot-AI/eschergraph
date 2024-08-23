from __future__ import annotations

import os

import networkx as nx
import seaborn as sns
from pyvis.network import Network

from eschergraph.graph import Edge
from eschergraph.graph import Node


def visualize_community_graph(comms: list[list[Node]], edges: list[Edge]) -> None:
  """Visualize a graph of communities.

  Communities are provided in a list containing lists of nodes, where each
  list of nodes corresponds to a community.

  Args:
    comms (list[list[node]]): A list of communities.
    edges (list[Edge]): The list of edges in the community graph.
  """
  nx_g: nx.Graph = _create_nx_graph(comms, edges)
  comm_colors: list[dict[str, str | int]] = _community_to_colors([
    [n.name for n in comm] for comm in comms
  ])

  # Add the color properties to the nx graph
  for nc in comm_colors:
    nx_g.nodes[nc["name"]]["group"] = nc["group"]
    nx_g.nodes[nc["name"]]["color"] = nc["color"]
    nx_g.nodes[nc["name"]]["size"] = nx_g.degree(nc["name"])

  _store_and_show_graph(nx_g)


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


def _create_nx_graph(comms: list[list[Node]], edges: list[Edge]) -> nx.Graph:
  graph: nx.Graph = nx.Graph()
  # Add the nodes and edges to the graph
  for comm in comms:
    for node in comm:
      graph.add_node(node.name)

  for edge in edges:
    graph.add_edge(edge.frm.name, edge.to.name, title=edge.description)

  return graph


def _get_output_directory() -> str:
  current_dir = os.path.dirname(os.path.abspath(__file__))
  graph_output_directory = os.path.join(current_dir, "docs", "index.html")
  return graph_output_directory


def _store_and_show_graph(graph: nx.Graph) -> None:
  net = Network(
    notebook=False,
    cdn_resources="remote",
    height="900px",
    width="100%",
    select_menu=True,
    filter_menu=False,
  )
  net.from_nx(graph)
  net.force_atlas_2based(central_gravity=0.015, gravity=-31)
  net.show_buttons(filter_=["physics"])

  net.show(_get_output_directory(), notebook=False)
