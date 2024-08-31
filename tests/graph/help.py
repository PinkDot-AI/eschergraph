from __future__ import annotations

import random
from typing import Optional
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

from faker import Faker

from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.graph import Edge
from eschergraph.graph import Graph
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.graph.persistence import Metadata
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.vector_db import VectorDB

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
    repository.get_node_by_name.return_value = None

  num_properties: int = random.randint(0, 150)
  metadata: Metadata = Metadata(document_id=uuid4(), chunk_id=random.randint(1, 120))

  node: Node = Node.create(
    name=faker.name(),
    description=faker.text(max_nb_chars=400),
    level=0,
    repository=repository,
    metadata={metadata},
  )

  for _ in range(num_properties):
    Property.create(
      node=node, description=faker.text(max_nb_chars=80), metadata={metadata}
    )

  return node


def create_property(
  node: Optional[Node] = None, repository: Optional[Repository] = None
) -> Property:
  if not node:
    node: Node = create_basic_node(repository=repository)
  return Property.create(node=node, description=faker.text(max_nb_chars=80))


def create_edge(
  frm: Optional[Node] = None,
  to: Optional[Node] = None,
  repository: Optional[Repository] = None,
) -> Edge:
  # If a repository is not specified, then use a mock
  if not repository:
    repository = MagicMock(spec=Repository)
    repository.get_node_by_name.return_value = None

  # Create an edge without specifying nodes
  if not frm:
    frm = create_basic_node(repository=repository)

  if not to:
    to = create_basic_node(repository=repository)

  return Edge.create(
    frm=frm,
    to=to,
    description=faker.text(max_nb_chars=80),
    metadata={Metadata(document_id=uuid4(), chunk_id=random.randint(1, 120))},
  )


def create_simple_extracted_graph(
  repository: Optional[Repository] = None,
) -> tuple[Graph, list[Node], list[Edge]]:
  # The mock repository as default, does not make much sense for this function
  if not repository:
    repository = MagicMock(spec=Repository)
    repository.get_node_by_name.return_value = None

  model_mock: MagicMock = MagicMock(spec=ModelProvider)
  reranker_mock: MagicMock = MagicMock(spec=Reranker)
  vector_db_mock: MagicMock = MagicMock(spec=VectorDB)

  model_mock.required_credentials = []
  reranker_mock.required_credentials = []
  vector_db_mock.required_credentials = []

  graph: Graph = Graph(
    name="test_graph",
    repository=repository,
    model=model_mock,
    reranker=reranker_mock,
    vector_db=vector_db_mock,
  )
  nodes: list[Node] = []
  edges: list[Edge] = []

  # Start by simulating a document
  document_id: UUID = uuid4()
  num_chunks: int = random.randint(3, 20)

  metadata: list[Metadata] = [
    Metadata(document_id=document_id, chunk_id=i) for i in range(num_chunks)
  ]

  num_nodes: int = random.randint(35, 100)
  for _ in range(num_nodes):
    # Create the node data with the mock repository
    node_data: Node = create_basic_node()

    node: Node = graph.add_node(
      name=node_data.name,
      description=node_data.description,
      level=node_data.level,
      metadata=random.choice(metadata),
    )

    num_properties: int = random.randint(5, 20)
    for _ in range(num_properties):
      property: Property = create_property(node=node, repository=repository)
      repository.add(property)

    nodes.append(node)

  num_edges: int = random.randint(80, 200)
  valid_pairs: list[tuple[int, int]] = [
    (a, b) for a in range(num_nodes) for b in range(a, num_nodes) if a != b
  ]

  for _ in range(min(num_edges, len(valid_pairs))):
    pair: tuple[int, int] = random.choice(valid_pairs)
    valid_pairs.remove(pair)

    edges.append(
      graph.add_edge(
        frm=nodes[pair[0]],
        to=nodes[pair[1]],
        description=faker.text(max_nb_chars=80),
        metadata=random.choice(metadata),
      )
    )

  return graph, nodes, edges


def create_node_only_multi_level_graph(
  max_level: int,
  repository: Optional[Repository] = None,
) -> Graph:
  """Create a graph with multiple levels, the graph makes no sense, as the nodes are not connected
  in any way.

  Args:
      max_level (int): Max level of a node
      repository (Optional[Repository], optional): Repository to be used. Defaults to None.

  Returns:
      Graph: The created graph
  """
  if not repository:
    repository = MagicMock(spec=Repository)

  model_mock: MagicMock = MagicMock(spec=ModelProvider)
  reranker_mock: MagicMock = MagicMock(spec=Reranker)
  vector_db_mock: MagicMock = MagicMock(spec=VectorDB)

  model_mock.required_credentials = []
  reranker_mock.required_credentials = []
  vector_db_mock.required_credentials = []

  graph: Graph = Graph(
    name="mutli_level_graph",
    repository=repository,
    model=model_mock,
    reranker=reranker_mock,
    vector_db=vector_db_mock,
  )
  document_id: UUID = uuid4()
  num_chunks: int = random.randint(5, 20)

  metadata: list[Metadata] = [
    Metadata(document_id=document_id, chunk_id=i) for i in range(num_chunks)
  ]
  # Make max_level occur multiple times and increase by one because of modulo operation
  num_nodes: int = random.randint((max_level + 1) * 4, 100)
  for i in range(num_nodes):
    node_data: Node = create_basic_node(repository=repository)

    graph.add_node(
      name=node_data.name,
      description=node_data.description,
      level=i % (max_level + 1),
      metadata=random.choice(metadata),
    )

  return graph
