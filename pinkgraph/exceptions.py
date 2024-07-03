from __future__ import annotations


class BasePinkgraphException(Exception):
  """The base class for all Pinkgraph exceptions."""


class PromptFormattingException(BasePinkgraphException):
  """When some jinja prompt variables have not been formatted.

  Used to check if the prompt has been sent to the LLM / agent as intended.
  """


class ExternalProviderException(BasePinkgraphException):
  """When something unexpected occurs during an interation with an external service."""
