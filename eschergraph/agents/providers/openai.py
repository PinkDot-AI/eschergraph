from __future__ import annotations

import json
from enum import Enum

from attrs import define
from openai import NotGiven
from openai import OpenAI
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionSystemMessageParam
from openai.types.chat import ChatCompletionToolChoiceOptionParam
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.shared_params import FunctionDefinition
from openai.types.shared_params import FunctionParameters
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_random_exponential

from eschergraph.agents.embedding import Embedding
from eschergraph.agents.llm import FunctionCall
from eschergraph.agents.llm import Model
from eschergraph.agents.llm import TokenUsage
from eschergraph.agents.tools import Function
from eschergraph.agents.tools import Tool
from eschergraph.exceptions import CredentialException
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
  TEXT_EMBEDDING_LARGE: str = "text-embedding-3-large"


@define(kw_only=True)
class ChatGPT(Model, Embedding):
  """The class that handles communication with the OpenAI API."""

  model: OpenAIModel
  api_key: str

  @property
  def client(self) -> OpenAI:
    """The OpenAI client."""
    if not self.api_key:
      raise CredentialException("No API key has been set")
    return OpenAI(api_key=self.api_key)

  @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
  def get_plain_response(self, prompt: str) -> str | None:
    """Get a text response from OpenAI.

    Note that the model that is used is specified when instantiating the class.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.

    Returns:
      The answer given or None.
    """
    return self._get_response(prompt)

  @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
  def get_formatted_response(
    self, prompt: str, response_format: ResponseFormat
  ) -> str | None:
    """Get a formatted response from OpenAI.

    Args:
      prompt (str): The user prompt that is send to ChatGPT.
      response_format (dict): Type of format that will be returned

    Returns:
      Formatted answer
    """
    return self._get_response(prompt=prompt, response_format=response_format)

  def _get_response(
    self,
    prompt: str,
    response_format: ResponseFormat | NotGiven = NotGiven(),
  ) -> str | None:
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

  def get_embedding(self, text_list: list[str]) -> list[list[float]]:
    """Generates embeddings for a list of text inputs using a specified model.

    This method takes a list of strings, processes each string by replacing newline characters with spaces,
    and then sends the processed list to a model to generate embeddings. If the input list is empty, it returns
    a list containing an empty list.

    Args:
        text_list (list[str]): A list of text strings for which embeddings are to be generated.

    Returns:
        list[list[float]]: A list of embeddings, where each embedding is a list of floats corresponding to
        the input text. If the input list is empty, returns a list containing an empty list.
    """
    # Handle empty lists
    if not len(text_list) > 0:
      return [[]]

    model = "text-embedding-3-large"
    text_list = [t.replace("\n", " ") for t in text_list]
    response = self.client.embeddings.create(input=text_list, model=model).data
    return [e.embedding for e in response]

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
