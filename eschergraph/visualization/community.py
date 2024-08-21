from __future__ import annotations

from typing import Optional

import seaborn as sns
from pyvis.network import Network

from eschergraph.graph import Edge
from eschergraph.graph import Node


def visualize_community_graph(
  comms: list[list[Node]],
  edges: list[Edge],
  save_location: Optional[str] = "community_visual.html",
) -> None:
  """Visualize a graph of communities.

  Communities are provided in a list containing lists of nodes, where each
  list of nodes corresponds to a community.

  Args:
    comms (list[list[node]]): A list of communities.
    edges (list[Edge]): The list of edges in the community graph.
    save_location (Optional[str]): The location to save the generated visual.
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

  for idx, comm in enumerate(comms):
    for nd in comm:
      net.add_node(
        str(nd.id),
        label=nd.name,
        title=nd.description,
        value=len(nd.edges),
        color=palette[idx],
      )

  for edge in edges:
    net.add_edge(str(edge.frm.id), str(edge.to.id), title=edge.description)

  net.force_atlas_2based(central_gravity=0.015, gravity=-31)
  net.show_buttons(filter_=["physics"])

  net.show(name=save_location, notebook=False)
