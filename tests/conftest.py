from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest
from pytest import TempPathFactory

from eschergraph.graph.persistence import Repository


@pytest.fixture(scope="function")
def mock_repository() -> Mock:
  mock: MagicMock = MagicMock(spec=Repository)
  mock.get_node_by_name.return_value = None

  return mock


@pytest.fixture(scope="function")
def saved_graph_dir(tmp_path_factory: TempPathFactory) -> Path:
  return tmp_path_factory.mktemp("saved_graph")
