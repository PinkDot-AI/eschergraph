from __future__ import annotations

from unittest.mock import create_autospec

import pytest

from eschergraph.graph.persistence import Repository


@pytest.fixture(scope="function")
def mock_repository() -> Repository:
  return create_autospec(spec=Repository, spec_set=True, instance=True)  # type: ignore
