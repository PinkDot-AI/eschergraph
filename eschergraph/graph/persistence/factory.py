from __future__ import annotations

from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.repository import Repository


def get_default_repository() -> Repository:
  """Return the default repository for initialization if a graph.

  Returns:
    The SimpleRepository with default settings.
  """
  return SimpleRepository()
