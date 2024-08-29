from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from attrs import define
from attrs import field


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


@define
class ModelProvider(ABC):
  """The abstract base class for all the LLMs used in the package."""

  required_credentials: list[str] = ["OPENAI_API_KEY"]
  tokens: list[TokenUsage] = field(factory=list)
  max_threads: int = field(default=10)

  @abstractmethod
  def get_model_name(self) -> str:
    """Get the model name of the model provider.

    Returns:
      The string name of the used llm model
    """
    raise NotImplementedError

  @abstractmethod
  def get_plain_response(self, prompt: str) -> str | None:
    """Get a plain text response from an LLM.

    Args:
      prompt (str): The prompt to send to the LLM.

    Returns:
      The response from the LLM.
    """
    raise NotImplementedError

  @abstractmethod
  def get_formatted_response(self, prompt: str, response_format: Any) -> str | None:
    """Get a formatted response from an LLM.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.
      response_format (dict): Type of format that will be returned

    Returns:
      Formatted answer
    """
    raise NotImplementedError

  @abstractmethod
  def get_json_response(self, prompt: str) -> dict[str, Any]:
    """Get a JSON response from an LLM.

    The JSON output is parsed into a Python dictionary before it is returned.

    Args:
      prompt (str): The prompt to send to the LLM.

    Returns:
      The parsed dictionary object.
    """
    raise NotImplementedError
