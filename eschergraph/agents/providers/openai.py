from __future__ import annotations

import json
import os
from enum import Enum

from attrs import define
from openai import OpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionToolChoiceOptionParam
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.shared_params import FunctionDefinition
from openai.types.shared_params import FunctionParameters
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential

from eschergraph.agents.llm import FunctionCall
from eschergraph.agents.llm import Model
from eschergraph.agents.llm import TokenUsage
from eschergraph.agents.tools import Function
from eschergraph.agents.tools import Tool
from eschergraph.exceptions import ExternalProviderException

SYSTEM_MESSAGE: str = """
You are an agent that will use tools to parse all the data
from any document into a refined and parsed form.
"""


class OpenAIModel(Enum):
  """The different models that are available at OpenAI."""

  GPT_3: str = "gpt-3.5-turbo"
  GPT_4o: str = "gpt-4o"
  GPT_4o_MINI: str = "gpt-4o-mini"


@define
class ChatGPT(Model):
  """The class that handles communication with the OpenAI API."""

  model: OpenAIModel
  client: OpenAI = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

  @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
  def get_plain_response(self, prompt: str) -> str | None:
    """Get a text response from ChatGPT.

    Note that the model that is used is specified when instantiating the class.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.

    Returns:
      The answer given or None.
    """
    messages: list[ChatCompletionMessageParam] = self._get_messages(prompt)
    messages.append(
      ChatCompletionSystemMessageParam(role="system", content=SYSTEM_MESSAGE)
    )
    messages.append(ChatCompletionUserMessageParam(role="user", content=prompt))
    try:
      response: ChatCompletion = self.client.chat.completions.create(
        model=self.model.value,
        messages=messages,
      )
      # Log the tokens that were used
      self._add_token_usage(response)
      return response.choices[0].message.content
    except Exception as e:
      raise ExternalProviderException(e)

  def get_function_calls(self, prompt: str, tools: list[Tool]) -> list[FunctionCall]:
    """Get function calls from ChatGPT.

    Collect function calls that the model chooses from the tools that are provided.

    Args:
      prompt (str): The instructions that explain the context under which tools should be used.
      tools (list[Tool]): The tools that are available.

    Returns:
      A list of function calls.
    """
    tool_choice: ChatCompletionToolChoiceOptionParam = "required"
    chat_tools: list[ChatCompletionToolParam] = self._get_tools_for_chat(tools)
    messages: list[ChatCompletionMessageParam] = self._get_messages(prompt)
    try:
      response: ChatCompletion = self.client.chat.completions.create(
        model=self.model.value,
        messages=messages,
        tools=chat_tools,
        tool_choice=tool_choice,
      )
      # Log the tokens that were used
      self._add_token_usage(response)
    except Exception as e:
      raise ExternalProviderException(e)

    # Convert the function calls to the package format
    function_calls: list[FunctionCall] = []

    chat_tool_response: list[ChatCompletionMessageToolCall] | None = response.choices[
      0
    ].message.tool_calls

    # In case Chat supplied no tool calls
    if not chat_tool_response:
      return function_calls

    chat_tool_calls: list[ChatCompletionMessageToolCall] = chat_tool_response

    for tool_call in chat_tool_calls:
      function_calls.append(
        FunctionCall(
          name=tool_call.function.name,
          arguments=json.loads(tool_call.function.arguments),
        )
      )

    return function_calls

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
