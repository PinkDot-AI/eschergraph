from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from uuid import UUID


class Repository[T](ABC):
  """An abstract base class for a repository as used in this package."""

  @abstractmethod
  def get(self, id: UUID) -> T:
    """Getting the object by id.

    Args:
      id (UUID): The id of the object.

    Returns:
      The (loaded) object from the repository.
    """
    raise NotImplementedError
