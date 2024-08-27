from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest
from pytest import TempPathFactory

from eschergraph.agents.llm import ModelProvider
from eschergraph.graph import Graph
from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.vector_db import VectorDB


@pytest.fixture(scope="function")
def mock_repository() -> Mock:
  mock: MagicMock = MagicMock(spec=Repository)
  mock.get_node_by_name.return_value = None

  return mock


@pytest.fixture(scope="function")
def saved_graph_dir(tmp_path_factory: TempPathFactory) -> Path:
  return tmp_path_factory.mktemp("saved_graph")


# Create a graph for unit testing
@pytest.fixture(scope="function")
def graph_unit() -> Graph:
  model: MagicMock = MagicMock(spec=ModelProvider)
  reranker: MagicMock = MagicMock(spec=ModelProvider)
  vector_db: MagicMock = MagicMock(spec=VectorDB)
  repository: MagicMock = MagicMock(spec=Repository)

  # Set the required credentials to an empty list
  model.required_credentials = []
  reranker.required_credentials = []
  vector_db.required_credentials = []

  return Graph(
    model=model, reranker=reranker, repository=repository, vector_db=vector_db
  )
