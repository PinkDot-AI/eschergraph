from __future__ import annotations

import random
from typing import Optional
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

from faker import Faker

from eschergraph.graph import Edge
from eschergraph.graph import Graph
from eschergraph.graph import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository

faker: Faker = Faker()


def create_basic_node(repository: Optional[Repository] = None) -> Node:
  """The helper function that creates a basic node.

  This refers to a node that is extracted directly from a source document
  as occurs in the pipeline.

  Args:
    repository (Optional[Repository]): The repository that persists the nodes.

  Returns:
    A random node that is similar to an extracted one.
  """
  # If a repository is not specified, then use a mock
  if not repository:
    repository = MagicMock(spec=Repository)

  num_properties: int = random.randint(0, 150)

  if num_properties == 0:
    properties: None | list[str] = None
  else:
    properties = [faker.text(max_nb_chars=100) for _ in range(num_properties)]

  return Node.create(
    name=faker.name(),
    description=faker.text(max_nb_chars=400),
    level=0,
    repository=repository,
    properties=properties,
    metadata={Metadata(document_id=uuid4(), chunk_id=random.randint(1, 120))},
  )


def create_edge(
  frm: Optional[Node] = None,
  to: Optional[Node] = None,
  repository: Optional[Repository] = None,
) -> Edge:
  # If a repository is not specified, then use a mock
  if not repository:
    repository = MagicMock(spec=Repository)

  # Create an edge without specifying nodes
  if not frm:
    frm = create_basic_node(repository=repository)

  if not to:
    to = create_basic_node(repository=repository)

  return Edge.create(
    frm=frm,
    to=to,
    repository=repository,
    description=faker.text(max_nb_chars=80),
    metadata={Metadata(document_id=uuid4(), chunk_id=random.randint(1, 120))},
  )


def create_simple_extracted_graph(
  repository: Optional[Repository] = None,
) -> tuple[Graph, list[Node], list[Edge]]:
  # The mock repository as default, does not make much sense for this function
  if not repository:
    repository = MagicMock(spec=Repository)

  graph: Graph = Graph(name="test_graph", repository=repository)
  nodes: list[Node] = []
  edges: list[Edge] = []

  # Start by simulating a document
  document_id: UUID = uuid4()
  num_chunks: int = random.randint(3, 20)

  for i in range(num_chunks):
    metadata: Metadata = Metadata(document_id=document_id, chunk_id=i)

    num_nodes: int = random.randint(1, 15)
    for _ in range(num_nodes):
      node_data: Node = create_basic_node(repository=repository)

      nodes.append(
        graph.add_node(
          name=node_data.name,
          description=node_data.description,
          level=node_data.level,
          metadata=metadata,
          properties=node_data.properties,
        )
      )

    num_edges: int = random.randint(3, 30)
    valid_pairs: list[tuple[int, int]] = [
      (a, b) for a in range(num_nodes) for b in range(a, num_nodes) if a != b
    ]

    for _ in range(min(num_edges, len(valid_pairs))):
      pair: tuple[int, int] = random.choice(valid_pairs)
      valid_pairs.remove(pair)

      edge_data: Edge = create_edge(frm=nodes[pair[0]], to=nodes[pair[1]])

      edges.append(
        graph.add_edge(
          frm=nodes[pair[0]],
          to=nodes[pair[1]],
          description=edge_data.description,
          metadata=metadata,
        )
      )

  return graph, nodes, edges
