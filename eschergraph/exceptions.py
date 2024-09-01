from __future__ import annotations


class BaseEscherGraphException(Exception):
  """The base class for all EscherGraph exceptions."""


class PromptFormattingException(BaseEscherGraphException):
  """When some jinja prompt variables have not been formatted.

  Used to check if the prompt has been sent to the LLM / agent as intended.
  """


class IllogicalActionException(BaseEscherGraphException):
  """When something unlogical happens, like searching before building a graph."""


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


class CredentialException(BaseEscherGraphException):
  """Missing credential for external provider."""


class FileTypeNotProcessableException(BaseEscherGraphException):
  """When a file is not processable due to its type."""


class EdgeDoesNotExistException(BaseEscherGraphException):
  """The specified edge could not be found."""


class RepositoryException(BaseEscherGraphException):
  """When something unexpected happens with the repository."""


class ExternalDependencyException(BaseEscherGraphException):
  """When an external dependency (outside of Python) is missing."""


class DocumentDoesNotExistException(BaseEscherGraphException):
  """When the specified document does not exist in the graph."""
