from __future__ import annotations


class BaseEscherGraphException(Exception):
  """The base class for all Pinkgraph exceptions."""


class PromptFormattingException(BaseEscherGraphException):
  """When some jinja prompt variables have not been formatted.

  Used to check if the prompt has been sent to the LLM / agent as intended.
  """


class ExternalProviderException(BaseEscherGraphException):
  """When something unexpected occurs during an interation with an external service."""


class DataLoadingException(BaseEscherGraphException):
  """Raised when some data on the EscherGraph objects has not been loaded as expected."""


class NodeDoesNotExistException(BaseEscherGraphException):
  """The specified node has not been found."""


class EdgeCreationException(BaseEscherGraphException):
  """When an edge is created between a node and itself."""


class NodeCreationException(BaseEscherGraphException):
  """When something goes wrong creating a node."""
