from __future__ import annotations

from typing import Optional

from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.repository import Repository


def get_default_repository(name: Optional[str] = None) -> Repository:
  """Return the default repository for initialization if a graph.

  Returns:
    The SimpleRepository with default settings.
  """
  return SimpleRepository(name=name)  # type: ignore
