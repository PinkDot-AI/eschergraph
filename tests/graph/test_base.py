from __future__ import annotations

from unittest.mock import Mock
from uuid import UUID

from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState


def test_escherbase_creation(mock_repository: Mock) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  assert isinstance(base.id, UUID)


def test_escherbase_metadata_initial(mock_repository: Mock) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  assert not base._metadata


def test_loadstate_setter(mock_repository: Mock) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  base.loadstate = LoadState.CORE

  mock_repository.load.assert_called_once()
  mock_repository.load.assert_called_with(base, loadstate=LoadState.CORE)


def test_loadstate_setter_decrease(mock_repository: Mock) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  base.loadstate = LoadState.FULL

  # Nothing should be done if the loadstate is decreased
  base.loadstate = LoadState.CORE

  mock_repository.load.assert_called_once()
  mock_repository.load.assert_called_with(base, loadstate=LoadState.FULL)
  assert base.loadstate == LoadState.FULL
