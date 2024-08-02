from __future__ import annotations

from unittest.mock import create_autospec
from uuid import UUID

import pytest

from eschergraph.graph.base import EscherBase
from eschergraph.graph.persistence import Repository


@pytest.fixture(scope="function")
def mock_repository() -> Repository:
  return create_autospec(spec=Repository, spec_set=True, instance=True)  # type: ignore


def test_escherbase_creation(mock_repository: Repository) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  assert isinstance(base.id, UUID)


def test_escherbase_metadata_initial(mock_repository: Repository) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  print(base._check_loadstate.__annotations__)
  assert not base._metadata


# Now added by the decorator so need to add that!!
# def test_check_loadstate_metadata(mock_repository: Repository) -> None:
#   # Set the metadata equal to an empty set
#   def load_side_effect(base: EscherBase, loadstate: LoadState) -> None:
#     base._metadata = set()

#   mock_repository.load.side_effect = load_side_effect
#   base: EscherBase = EscherBase(repository=mock_repository)

#   assert isinstance(base.metadata, set)
#   assert base.loadstate == LoadState.CORE
