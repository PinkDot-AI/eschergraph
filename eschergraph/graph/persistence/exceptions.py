from __future__ import annotations

from eschergraph.exceptions import BaseEscherGraphException


class PersistenceException(BaseEscherGraphException):
  """The base class for all EscherGraph exceptions that relate to persistence."""
