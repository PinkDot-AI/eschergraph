from __future__ import annotations

from abc import ABC
from typing import Callable
from typing import Optional

from attrs import define


class Tool(ABC):
  """The base class for a tool.

  Any tool that an agent can interact with.
  """

  executor: Callable[..., None]


@define
class Parameter:
  """The class for a function parameter.

  Includes all the information that an agent needs about the
  function arguments.
  """

  name: str
  type: str
  description: str
  enum: Optional[list[str]] = None
  is_required: bool = False

  def to_key(self) -> str:
    """Returns the name of the parameter."""
    return self.name

  def to_value(self) -> dict[str, str | list[str]]:
    """Returns the value of the parameter in the description."""
    result: dict[str, str | list[str]] = {
      "type": self.type,
      "description": self.description,
    }

    if self.enum:
      result.update({"enum": self.enum})

    return result


@define
class Function(Tool):
  """A function that an agent can interact with.

  A function that the agent can execute with the required information
  added.
  """

  name: str
  description: str
  parameters: list[Parameter]
  required: list[str]
