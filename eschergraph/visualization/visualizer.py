from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING
from uuid import UUID

import seaborn as sns
from pyvis.network import Network

from eschergraph.graph import Edge

if TYPE_CHECKING:
  from eschergraph.graph import Graph
  from eschergraph.graph import Node


# TODO: add level and graph name to the visualization
class Visualizer:
  """The visualizer for EscherGraphs."""

  @staticmethod
  def visualize_graph(
    graph: Graph, level: int = 0, save_location: str = "graph_visual.html"
  ) -> None:
    """Visualize a level of a graph.

    Args:
      graph (Graph): The graph to visualize.
      level (int): The level of the graph that needs to be visualized.
      save_location (str): The location to save the generated visual.
    """
    # Transform the list of node_ids into a list of nodes
    if level < 2:
      comms: list[list[Node]] = [
        comm.child_nodes for comm in graph.repository.get_all_at_level(level + 1)
      ]
    else:
      comms: list[list[Node]] = [
        [node] for node in graph.repository.get_all_at_level(2)
      ]

    print(comms)
    edges: list[Edge] = [edge for comm in comms for node in comm for edge in node.edges]

    Visualizer.visualize_community_graph(
      comms=comms, edges=edges, save_location=save_location
    )

  @staticmethod
  def visualize_community_graph(
    comms: list[list[Node]],
    edges: list[Edge],
    save_location: str = "community_visual.html",
  ) -> None:
    """Visualize a graph of communities.

    Communities are provided in a list containing lists of nodes, where each
    list of nodes corresponds to a community.

    Args:
      comms (list[list[node]]): A list of communities.
      edges (list[Edge]): The list of edges in the community graph.
      save_location (str): The location to save the generated visual.
    """
    palette: list[str] = sns.color_palette("hls", len(comms)).as_hex()
    net = Network(
      notebook=False,
      cdn_resources="remote",
      height="900px",
      width="100%",
      select_menu=True,
      filter_menu=False,
    )

    # Map all nodes in comms to their id for lookup
    node_id: dict[UUID, Node] = {nd.id: nd for comm in comms for nd in comm}

    for idx, comm in enumerate(comms):
      for nd in comm:
        net.add_node(
          nd.name,
          label=nd.name,
          title=nd.description,
          value=len(nd.edges),
          color=palette[idx],
        )

    for edge in edges:
      net.add_edge(
        node_id[edge.frm.id].name, node_id[edge.to.id].name, title=edge.description
      )

    net.force_atlas_2based(central_gravity=0.015, gravity=-31)
    net.show_buttons(filter_=["physics"])

    html_content = net.generate_html()
    with open(save_location, "w", encoding="utf-8") as f:
      f.write(html_content)

    webbrowser.open(save_location)
