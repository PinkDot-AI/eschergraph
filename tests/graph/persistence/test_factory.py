from __future__ import annotations

from eschergraph.graph.persistence import Repository
from eschergraph.graph.persistence.factory import get_default_repository


def test_getting_default_repository() -> None:
  assert isinstance(get_default_repository(), Repository)
