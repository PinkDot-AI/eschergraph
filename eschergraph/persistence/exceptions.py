from __future__ import annotations

from eschergraph.exceptions import BaseEscherGraphException


class PersistenceException(BaseEscherGraphException):
  """The base class for all EscherGraph exceptions that relate to persistence."""


class DirectoryDoesNotExistException(PersistenceException):
  """The specified directory does not exist."""


class FilesMissingException(PersistenceException):
  """Some files are missing or corrupted."""


class PersistingEdgeException(PersistenceException):
  """Both referenced nodes need to exist when an edge is persisted directly."""
