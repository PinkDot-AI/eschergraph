from __future__ import annotations

import json
from uuid import UUID

from eschergraph.agents.jinja_helper import process_template
from eschergraph.config import COMMUNITY_TEMPLATE
from eschergraph.config import TEMPLATE_IMPORTANCE
from eschergraph.exceptions import EdgeDoesNotExistException
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph import Edge
from eschergraph.graph import Graph
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.graph.comm_graph import CommunityGraphResult
from eschergraph.graph.community_alg import get_leidenalg_communities


class CommunityBuilder:
  """The community builder.

  Builds an extra top layer of communities on a level of the graph.
  """

  @staticmethod
  def build(level: int, graph: Graph) -> None:
    """Build a community layer in a new level of the graph.

    Args:
      level (int): Which level to build on top of.
      graph (Graph): The graph to build a community layer for.
    """
    nodes: list[Node] = graph.repository.get_all_at_level(level)
    comms: CommunityGraphResult = get_leidenalg_communities(nodes)

    # Transform nodes of graph to dict for faster lookup
    node_lookup: dict[UUID, Node] = {nd.id: nd for nd in nodes}
    # Map every node to its community
    node_comm: dict[UUID, int] = {
      nd: idx for idx, comm in enumerate(comms.partitions) for nd in comm
    }

    edges: list[Edge] = []
    # Create an empty community node for each community
    nodes_tmp: dict[int, Node] = {
      idx: CommunityBuilder._create_empty_community_node(
        graph, comms.partitions[idx], level
      )
      for idx in set(node_comm.values())
    }

    # Add edges between community nodes
    for edge_id in comms.edges:
      edge = graph.repository.get_edge_by_id(edge_id)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")

      frm: int = node_comm[edge.frm.id]
      to: int = node_comm[edge.to.id]

      # Only use the edges that exist between communities
      if frm == to:
        continue

      new_edge = Edge.create(frm=nodes_tmp[frm], to=nodes_tmp[to], description="")
      edges.append(new_edge)

    # Generate and process findings for each community
    for comm_idx in nodes_tmp.keys():
      comm_edges: list[Edge] = CommunityBuilder._gather_community_edges(
        graph, comms.edges, comms.partitions[comm_idx]
      )
      comm_nodes: list[Node] = [
        node_lookup[nd_id] for nd_id in comms.partitions[comm_idx]
      ]

      title, description, findings = CommunityBuilder._get_model_findings(
        graph, comm_edges, comm_nodes
      )

      for finding in findings:
        Property.create(nodes_tmp[comm_idx], description=finding["explanation"])

      nodes_tmp[comm_idx].name = title
      nodes_tmp[comm_idx].description = description

      graph.repository.add(nodes_tmp[comm_idx])

  @staticmethod
  def _create_empty_community_node(
    graph: Graph, child_nodes: list[UUID], level: int
  ) -> Node:
    return Node.create(
      name="",
      description="",
      level=level + 1,
      repository=graph.repository,
      child_nodes=[
        node
        for node_id in child_nodes
        if (node := graph.repository.get_node_by_id(node_id)) and node is not None
      ],
    )

  @staticmethod
  def _gather_community_edges(
    graph: Graph, edges: list[UUID], nodes: list[UUID]
  ) -> list[Edge]:
    """Get all edges that are connected to a node from the node list.

    Args:
      graph (Graph): The graph that contains the edges and nodes.
      edges (list[UUID]): Edge id's to be filtered.
      nodes (list[UUID]): The nodes to which the edges should be connected.

    Returns:
      list[Edge]: A list of the filtered edges.
    """
    node_set = set(nodes)
    comm_edges = []
    for edge_id in edges:
      edge = graph.repository.get_edge_by_id(edge_id)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")
      if edge.frm.id in node_set or edge.to.id in node_set:
        comm_edges.append(edge)

    return comm_edges

  @staticmethod
  def _get_model_findings(
    graph: Graph, comm_edges: list[Edge], comm_nodes: list[Node]
  ) -> tuple[str, str, list[dict[str, str]]]:
    """Get the model findings for a new community node.

    Args:
      graph (Graph): The graph to which the community is added.
      comm_edges (list[Edge]): All the edges that are connected
        to a node from the community.
      comm_nodes (list[Node]): All the nodes that are in the community
        for which findings need to be generated.

    Returns:
      The name, description, and a list of findings for the community node.
    """
    prop_format: str = "node_name,property\n" + "\n".join(
      f"{node.name},{prop.description}"
      for node in comm_nodes
      for prop in node.properties
    )
    edge_format: str = "from,to,description\n" + "\n".join(
      f"{edge.frm.name},{edge.to.name},{edge.description}" for edge in comm_edges
    )

    finding_prompt = process_template(
      COMMUNITY_TEMPLATE,
      {
        "relationships": edge_format,
        "properties": prop_format,
      },
    )

    res = graph.model.get_formatted_response(finding_prompt, {"type": "json_schema"})
    if res is None:
      raise ExternalProviderException("Invalid response from LLM")
    parsed_json = json.loads(res)
    if (
      "title" not in parsed_json
      or "summary" not in parsed_json
      or "findings" not in parsed_json
    ):
      raise ExternalProviderException("LLM JSON Response did not contain correct keys")
    jsonized: str = json.dumps(parsed_json["findings"], indent=4)
    reorder_prompt = process_template(TEMPLATE_IMPORTANCE, {"json_list": jsonized})
    res_reorder = graph.model.get_formatted_response(
      prompt=reorder_prompt, response_format={"type": "json_schema"}
    )
    if res_reorder is None:
      raise ExternalProviderException("Invalid response from LLM for reordering")
    findings = json.loads(res_reorder)
    if not isinstance(findings, list):
      raise ExternalProviderException("Invalid response from LLM for reordering")

    return parsed_json["title"], parsed_json["description"], findings
