from __future__ import annotations

import random
from typing import Optional
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
from uuid import UUID

import pytest
from faker import Faker

from eschergraph.graph import Edge
from eschergraph.graph import Graph
from eschergraph.graph import Node
from eschergraph.graph.community_alg import CommunityGraphResult
from eschergraph.graph.community_alg import get_leidenalg_communities
from eschergraph.tools.community_builder import CommunityBuilder
from tests.graph.help import create_simple_extracted_graph

faker: Faker = Faker()


@pytest.fixture(scope="function")
def graph_communities_setup(
  mock_repository: Mock,
) -> tuple[Graph, list[Node], list[Edge]]:
  # Only nodes from level 0
  graph, nodes, edges = create_simple_extracted_graph(repository=mock_repository)
  node_dict: dict[UUID, Node] = {node.id: node for node in nodes}
  edge_dict: dict[UUID, Edge] = {edge.id: edge for edge in edges}

  # Side effect functions for get node and edge by id
  def node_by_id(id: UUID) -> Optional[Node]:
    if not id in node_dict:
      return None
    return node_dict[id]

  def edge_by_id(id: UUID) -> Optional[Edge]:
    if not id in edge_dict:
      return None
    return edge_dict[id]

  graph.repository.get_all_at_level.return_value = nodes
  graph.repository.get_edge_by_id.side_effect = edge_by_id
  graph.repository.get_node_by_id.side_effect = node_by_id

  return graph, nodes, edges


def generate_random_community_findings() -> tuple[str, str, dict[str, str]]:
  # Generate a random number of findings
  findings: list[dict[str, str]] = [
    {"summary": faker.text(max_nb_chars=80), "explanation": faker.text(max_nb_chars=80)}
    for _ in range(random.randint(1, 9))
  ]
  return faker.name(), faker.text(max_nb_chars=80), findings


def edges_between_communities(
  partitions: list[list[UUID]], edges: list[Edge]
) -> list[set[int]]:
  # Map each node_id to its partition number
  node_comms: dict[UUID, int] = {
    n_id: idx for idx, comm in enumerate(partitions) for n_id in comm
  }

  return [
    {node_comms[edge.frm.id], node_comms[edge.to.id]}
    for edge in edges
    if node_comms[edge.frm.id] != node_comms[edge.to.id]
  ]


def test_building_community_nodes(
  graph_communities_setup: tuple[Graph, list[Node], list[Edge]],
) -> None:
  graph, nodes, _ = graph_communities_setup
  # The number of communities for the asserts
  community_result: CommunityGraphResult = get_leidenalg_communities(nodes)
  num_comms: int = len(community_result.partitions)

  # The random findings for each community
  name, description, findings = generate_random_community_findings()
  mock_llm_findings: MagicMock = MagicMock()
  mock_llm_findings.return_value = name, description, findings

  # Reset the graph repository call_count
  graph.repository.add.call_count = 0
  graph.repository.add.call_args_list = []

  with patch.object(CommunityBuilder, "_get_model_findings", mock_llm_findings):
    CommunityBuilder.build(level=0, graph=graph)

  graph.repository.get_all_at_level.assert_called_once_with(0)
  assert mock_llm_findings.call_count == num_comms

  for idx, call in enumerate(graph.repository.add.call_args_list):
    node_added: Node = call[0][0]
    assert node_added.name == name
    assert node_added.description == description
    assert {prop.description for prop in node_added.properties} == {
      fd["explanation"] for fd in findings
    }
    assert node_added.level == 1
    assert {n.id for n in node_added.child_nodes} == set(
      community_result.partitions[idx]
    )

  assert graph.repository.add.call_count == num_comms


def test_building_community_edges(
  graph_communities_setup: tuple[Graph, list[Node], list[Edge]],
) -> None:
  graph, nodes, edges = graph_communities_setup
  # The number of communities for the asserts
  community_result: CommunityGraphResult = get_leidenalg_communities(nodes)
  edges_between_comms: list[set[int]] = edges_between_communities(
    partitions=community_result.partitions, edges=edges
  )

  # The random findings for each community
  mock_llm_findings: MagicMock = MagicMock()
  mock_llm_findings.return_value = generate_random_community_findings()

  # Reset the graph repository call_count
  graph.repository.add.call_count = 0
  graph.repository.add.call_args_list = []

  with patch.object(CommunityBuilder, "_get_model_findings", mock_llm_findings):
    CommunityBuilder.build(level=0, graph=graph)

  # Assert that the correct edges were added
  # Start by creating a dict that matches community node to community index
  node_comm: dict[Node, int] = {}
  nodes: list[Node] = []
  for idx, call in enumerate(graph.repository.add.call_args_list):
    node_added: Node = call[0][0]
    node_comm[node_added] = idx
    nodes.append(node_added)

  # Add all community pairs for the edges
  edges_comms: list[set[int]] = []
  for node in nodes:
    for edge in node.edges:
      frm_idx: int = node_comm[edge.frm]
      to_idx: int = node_comm[edge.to]
      if not {frm_idx, to_idx} in edges_comms:
        edges_comms.append({frm_idx, to_idx})

  for comm_pair in edges_comms:
    assert comm_pair in edges_between_comms

  for comm_pair in edges_between_comms:
    assert comm_pair in edges_comms
