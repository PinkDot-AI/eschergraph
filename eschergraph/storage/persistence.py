from __future__ import annotations

from uuid import UUID
from uuid import uuid4


# TODO: add a hash functionality to detect changes
def persistence(cls):
  """The decorator to augment a class for persistence.

  A decorator that can be used to give a class functionalities that are needed
  for persistence. This has been implemented as a decorator to separate the class
  from its persistence.
  """
  # Add the class attributes (with type hints) that are needed to manage persistence
  cls.persisted = False
  cls.__annotations__["persisted"] = bool

  cls.loaded = False
  cls.__annotations__["loaded"] = bool

  cls.id = uuid4()
  cls.__annotations__["id"] = UUID
