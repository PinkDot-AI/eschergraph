from __future__ import annotations

import json
import os
from enum import Enum
from typing import Any

from attrs import define
from attrs import field
from openai import NotGiven
from openai import OpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.shared_params import FunctionDefinition
from openai.types.shared_params import FunctionParameters
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential

from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.llm import TokenUsage
from eschergraph.agents.tools import Function
from eschergraph.agents.tools import Tool
from eschergraph.exceptions import CredentialException
from eschergraph.exceptions import ExternalProviderException

SYSTEM_MESSAGE: str = """
You are an agent that will use tools to parse all the data
from any document into a refined and parsed form.
"""


class GroqModel(Enum):
  """The different models that are available at OpenAI."""

  LLAMA3_1_8B: str = "llama-3.1-8b-instant"
  LLAMA_3_1_70B: str = "llama-3.1-70b-versatile"


@define
class GroqProvider(ModelProvider):
  """The class that handles communication with the OpenAI API."""

  model: GroqModel
  required_credentials: list[str] = ["GROQ_API_KEY"]
  tokens: list[TokenUsage] = field(factory=list)
  max_threads: int = field(default=10)

  @property
  def client(self) -> OpenAI:
    """The Groq client."""
    api_key: str = os.getenv("GROQ_API_KEY")
    if not api_key:
      raise CredentialException("No API key for Groq has been set")
    return OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)

  def get_model_name(self) -> str:
    """Returns which model is used.

    Returns:
      The given model name as a string
    """
    return self.model.value

  @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
  def get_plain_response(self, prompt: str) -> Any:
    """Get a text response from OpenAI.

    Note that the model that is used is specified when instantiating the class.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.

    Returns:
      The answer given or None.
    """
    return self._get_response(prompt)

  @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
  def get_formatted_response(self, prompt: str, response_format: ResponseFormat) -> Any:
    """Get a formatted response from OpenAI.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.
      response_format (dict): Type of format that will be returned

    Returns:
      Formatted answer
    """
    return self._get_response(prompt=prompt, response_format=response_format)

  @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
  def get_json_response(self, prompt: str) -> dict[str, Any]:
    """Get a json response.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.

    Returns:
      A json object parsed into a dictionary.
    """
    return json.loads(  # type: ignore
      self._get_response(prompt=prompt, response_format={"type": "json_object"})
    )

  def _get_response(
    self,
    prompt: str,
    response_format: ResponseFormat | NotGiven = NotGiven(),
  ) -> Any:
    messages: list[ChatCompletionMessageParam] = self._get_messages(prompt)

    try:
      response: ChatCompletion = self.client.chat.completions.create(
        model=self.model.value,
        messages=messages,
        response_format=response_format,
      )
      # Log the tokens that were used
      self._add_token_usage(response)
      return response.choices[0].message.content
    except Exception as e:
      print(e)
      raise ExternalProviderException(e)

  def _add_token_usage(self, response: ChatCompletion) -> None:
    if response.usage:
      completion_usage: CompletionUsage = response.usage
      self.tokens.append(
        TokenUsage(
          prompt_tokens=completion_usage.prompt_tokens,
          total_tokens=completion_usage.total_tokens,
          completion_tokens=completion_usage.completion_tokens,
        )
      )

  @staticmethod
  def _get_tools_for_chat(tools: list[Tool]) -> list[ChatCompletionToolParam]:
    chat_tools: list[ChatCompletionToolParam] = []
    for tool in tools:
      # Checking for the type, but only type Function is currently supported
      if not isinstance(tool, Function):
        continue

      function: Function = tool

      function_parameters: FunctionParameters = {
        "type": "object",
        "properties": {
          parameter.to_key(): parameter.to_value() for parameter in function.parameters
        },
        "required": [
          parameter.name for parameter in function.parameters if parameter.is_required
        ],
      }
      function_definition_chat: FunctionDefinition = FunctionDefinition({
        "name": function.name,
        "description": function.description,
        "parameters": function_parameters,
      })
      chat_function: ChatCompletionToolParam = ChatCompletionToolParam({
        "type": "function",
        "function": function_definition_chat,
      })

      chat_tools.append(chat_function)

    return chat_tools

  @staticmethod
  def _get_messages(prompt: str) -> list[ChatCompletionMessageParam]:
    messages: list[ChatCompletionMessageParam] = []
    messages.append(
      ChatCompletionSystemMessageParam(role="system", content=SYSTEM_MESSAGE)
    )
    messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))
    return messages
