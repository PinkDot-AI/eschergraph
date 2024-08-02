from __future__ import annotations

from uuid import UUID

from eschergraph.graph.base import EscherBase
from eschergraph.graph.persistence import Repository


def test_escherbase_creation(mock_repository: Repository) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  assert isinstance(base.id, UUID)


def test_escherbase_metadata_initial(mock_repository: Repository) -> None:
  base: EscherBase = EscherBase(repository=mock_repository)
  assert not base._metadata
