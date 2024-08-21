from __future__ import annotations

import random
from uuid import UUID

import pytest
from faker import Faker
from pytest import TempPathFactory

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.community_alg import get_leidenalg_communities
from tests.graph.help import create_simple_extracted_graph

faker: Faker = Faker()


@pytest.fixture(scope="function")
def node_name_comms() -> list[list[str]]:
  name_comms: list[list[str]] = []
  num_comms: int = 15
  for _ in range(num_comms):
    num_nodes: int = random.randint(3, 25)
    name_comms.append([faker.name() for _ in range(num_nodes)])

  return name_comms


@pytest.fixture(scope="function")
def community_graph() -> tuple[list[list[Node]], list[Edge]]:
  _, nodes, edges = create_simple_extracted_graph()
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
