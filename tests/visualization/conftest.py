from __future__ import annotations

from uuid import UUID

import pytest
from faker import Faker
from pytest import TempPathFactory

from eschergraph.graph import Edge
from eschergraph.graph import Graph
from eschergraph.graph import Node
from eschergraph.graph.community_alg import get_leidenalg_communities
from tests.graph.help import create_simple_extracted_graph

faker: Faker = Faker()


@pytest.fixture(scope="module")
def graph_visual() -> tuple[Graph, list[Node], list[Edge]]:
  return create_simple_extracted_graph()


@pytest.fixture(scope="module")
def community_graph(
  graph_visual: tuple[Graph, list[Node], list[Edge]],
) -> tuple[list[list[Node]], list[Edge]]:
  _, nodes, edges = graph_visual
  node_ids: list[list[UUID]] = get_leidenalg_communities(nodes).partitions

  node_dict: dict[UUID, Node] = {node.id: node for node in nodes}

  # Transform the list of node_ids into a list of nodes
  comms: list[list[Node]] = []
  for comm in node_ids:
    comm_nodes: list[Node] = []
    for id in comm:
      comm_nodes.append(node_dict[id])

    comms.append(comm_nodes)

  return comms, edges


@pytest.fixture(scope="function")
def visualization_dir(tmp_path_factory: TempPathFactory) -> str:
  return tmp_path_factory.mktemp("visualization").as_posix()
