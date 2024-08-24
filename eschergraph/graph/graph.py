from __future__ import annotations

import json
from collections import Counter
from typing import Optional
from uuid import UUID

from attrs import define
from attrs import field

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import Model
from eschergraph.exceptions import EdgeDoesNotExistException
from eschergraph.exceptions import ExternalProviderException
from eschergraph.exceptions import NodeDoesNotExistException
from eschergraph.graph.community import Finding
from eschergraph.graph.community import Report
from eschergraph.graph.community_alg import get_leidenalg_communities
from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository


@define
class Graph:
  """The EscherGraph graph class."""

  name: str
  repository: Repository = field(factory=get_default_repository)

  def add_node(
    self,
    name: str,
    description: str,
    level: int,
    metadata: Metadata,
    properties: Optional[list[str]] = None,
  ) -> Node:
    """Add a node to the graph.

    After creation, the node is persisted immediately to the repository.
    This is done as no data is saved in the graph object itself.

    Args:
      name (str): The name of the node.
      description (str): A description of the node.
      level (int): The level of the node.
      metadata (Metadata): The metadata of the node.
      properties (Optional[list[str]]): The optional properties of the node.

    Returns:
      The node that has been created.
    """
    node: Node = Node.create(
      name=name,
      description=description,
      level=level,
      repository=self.repository,
      properties=properties,
      metadata={metadata},
    )

    # Persist the node
    self.repository.add(node)

    return node

  def add_edge(self, frm: Node, to: Node, description: str, metadata: Metadata) -> Edge:
    """Add an edge to the graph.

    The edge is persisted to the repository straight away.

    Args:
      frm (Node): The from node in the edge.
      to (Node): The to node in the edge.
      description (str): A rich description of the relation.
      metadata (Metadata): The metadata of the edge.

    Returns:
      The edge that has been added to the graph.
    """
    edge: Edge = Edge.create(
      frm=frm,
      to=to,
      description=description,
      repository=self.repository,
      metadata={metadata},
    )

    # Persist the edge
    self.repository.add(edge)

    return edge

  def build_community_layer(self, from_level: int, llm: Model) -> None:
    """Build a community layer in a new level of the graph.

    Args:
        from_level (int): Which level to build on top of.
        llm (Model): LLM to create community reports

    """
    nodes = self.repository.get_all_at_level(from_level)
    comms = get_leidenalg_communities(nodes)

    # Transform nodes of graph to dict for faster lookup
    node_lookup = {nd.id: nd for nd in nodes}
    # Map every node to its community
    node_comm = {nd: idx for idx, comm in enumerate(comms.partitions) for nd in comm}

    node_count = Counter()  # type: ignore
    comm_max: dict[int, UUID] = {}

    # Count most node occurrences per community
    for edge_id in comms.edges:
      edge = self.repository.get_edge_by_id(edge_id)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")
      node_count[edge.frm.id] += 1
      node_count[edge.to.id] += 1
      comm1 = node_comm[edge.frm.id]
      comm2 = node_comm[edge.to.id]
      if comm1 not in comm_max or node_count[edge.frm.id] > node_count[comm_max[comm1]]:
        comm_max[comm1] = edge.frm.id
      if comm2 not in comm_max or node_count[edge.to.id] > node_count[comm_max[comm2]]:
        comm_max[comm2] = edge.to.id

    edges: list[Edge] = []
    nodes_tmp: dict[int, Node] = dict()
    # Add edges between community nodes
    for ed in comms.edges:
      edge = self.repository.get_edge_by_id(ed)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")
      frm = node_comm[edge.frm.id]
      to = node_comm[edge.to.id]
      # and len(comms[frm]) > 2 and len(comms[to]) > 2
      if frm != to:
        # Node descriptions will be given later
        if frm not in nodes_tmp:
          main_node = self.repository.get_node_by_id(comm_max[frm])
          if main_node is None:
            raise NodeDoesNotExistException()
          nodes_tmp[frm] = Node.create(
            name=main_node.name,
            description="",
            level=from_level + 1,
            repository=self.repository,
            child_nodes=[
              node
              for node_id in comms.partitions[frm]
              if (node := self.repository.get_node_by_id(node_id)) and node is not None
            ],
          )
        if to not in nodes_tmp:
          main_node = self.repository.get_node_by_id(comm_max[to])
          if main_node is None:
            raise NodeDoesNotExistException()
          nodes_tmp[to] = Node.create(
            name=main_node.name,
            description="",
            level=from_level + 1,
            repository=self.repository,
            child_nodes=[
              node
              for node_id in comms.partitions[to]
              if (node := self.repository.get_node_by_id(node_id)) and node is not None
            ],
          )
        # Edges bidirectional
        edges.append(
          Edge.create(
            frm=nodes_tmp[frm],
            to=nodes_tmp[to],
            description="",
            repository=self.repository,
          )
        )
        edges.append(
          Edge.create(
            frm=nodes_tmp[to],
            to=nodes_tmp[frm],
            description="",
            repository=self.repository,
          )
        )

    comm_template = "community_prompt.jinja"
    for k, v in nodes_tmp.items():
      idx = node_comm[v.id]
      prop_format = "node_name,property\n"
      formatted_props = [
        f"{node_lookup[nd_id].name},{prop}"
        for nd_id in comms.partitions[idx]
        for prop in node_lookup[nd_id].properties
      ]
      prop_format += "\n".join(formatted_props)

      edge_relations = self.gather_community_edges(
        self.repository, comms.edges, comms.partitions[idx]
      )
      edge_format = "from,to,description\n"
      formatted_edges = [
        f"{ed.frm.name},{ed.to.name},{ed.description}" for ed in edge_relations
      ]
      edge_format += "\n".join(formatted_edges)

      prompt = process_template(
        comm_template,
        {
          "relationships": edge_format,
          "properties": prop_format,
        },
      )

      res = llm.get_formatted_response(prompt, {"type": "json_schema"})
      if res is None:
        raise ExternalProviderException("No")
      parsed_json = json.loads(res)
      if (
        "title" not in parsed_json
        or "summary" not in parsed_json
        or "findings" not in parsed_json
      ):
        raise ExternalProviderException

      findings = [
        Finding(summary=finding["summary"], explanation=finding["explanation"])
        for finding in parsed_json["findings"]
      ]
      nodes_tmp[k].report = Report(
        title=parsed_json["title"], summary=parsed_json["summary"], findings=findings
      )

      self.repository.add(nodes_tmp[k])
    for edge in edges:
      self.repository.add(edge)

  @staticmethod
  def gather_community_edges(
    repository: Repository, edges: list[UUID], nodes: list[UUID]
  ) -> list[Edge]:
    """Get all edges that are connected to a node from the node list.

    Args:
        repository (Repository): The repository that is connected with the edges
        edges (list[UUID]): Edges to be filtered.
        nodes (list[UUID]): The nodes to which the edges should be connected

    Returns:
        list[Edge]: A list of the filtered edges.
    """
    node_set = set(nodes)
    comm_edges = []
    for edge_id in edges:
      edge = repository.get_edge_by_id(edge_id)
      if edge is None:
        raise EdgeDoesNotExistException(f"Edge {edge_id} could not be found")
      if edge.frm.id in node_set or edge.to.id in node_set:
        comm_edges.append(edge)

    return comm_edges
