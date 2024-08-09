from __future__ import annotations

import random
from typing import Optional
from unittest.mock import MagicMock
from uuid import uuid4

from faker import Faker

from eschergraph.graph import Edge
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


def create_edge(frm: Node, to: Node, repository: Optional[Repository] = None) -> Edge:
  # If a repository is not specified, then use a mock
  if not repository:
    repository = MagicMock(spec=Repository)

  return Edge.create(
    frm=frm,
    to=to,
    repository=repository,
    description=faker.text(max_nb_chars=80),
    metadata={Metadata(document_id=uuid4(), chunk_id=random.randint(1, 120))},
  )
