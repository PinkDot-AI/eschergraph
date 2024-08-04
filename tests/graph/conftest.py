from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import Mock

import pytest

from eschergraph.graph.persistence import Repository


@pytest.fixture(scope="function")
def mock_repository() -> Mock:
  return MagicMock(spec=Repository)
