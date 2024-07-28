from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from attrs import define
from attrs import field

from eschergraph.agents.tools import Tool


@define
class FunctionCall:
  """The function call as returned by the model.

  The arguments are a JSON representation of the arguments that need to be
  supplied to the function. They still need to be validated.
  """

  name: str
  arguments: dict[str, Any]


@define
class TokenUsage:
  """Information on the tokens used by the LLM."""

  prompt_tokens: int
  completion_tokens: int
  total_tokens: int


class Model(ABC):
  """The abstract base class for all the LLMs used in the package."""

  tokens: list[TokenUsage] = field(factory=list)

  @abstractmethod
  def get_plain_response(self, prompt: str) -> str | None:
    """Get a plain text response from an LLM.

    Args:
      prompt (str): The prompt to send to the LLM.

    Returns:
      The response from the LLM.
    """
    ...

  @abstractmethod
  def get_function_calls(self, prompt: str, tools: list[Tool]) -> list[FunctionCall]:
    """Get function calls from the model.

    Args:
      prompt (str): The prompt to send to the LLM.
      tools (list[Tool]): The list of tools (functions) that the agent can use.

    Returns:
      A list of function calls as specified by the model.
    """
    ...
