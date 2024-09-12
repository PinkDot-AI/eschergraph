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
  """Node has not been found."""


class EdgeCreationException(BaseEscherGraphException):
  """Edge is created between a node and itself."""


class NodeCreationException(BaseEscherGraphException):
  """Something went wrong creating a node."""


class CredentialException(BaseEscherGraphException):
  """Missing credential for external provider."""


class FileTypeNotProcessableException(BaseEscherGraphException):
  """File is not processable due to its type."""


class EdgeDoesNotExistException(BaseEscherGraphException):
  """The specified edge could not be found."""


class RepositoryException(BaseEscherGraphException):
  """Something unexpected happens with the repository."""


class ExternalDependencyException(BaseEscherGraphException):
  """External dependency (outside of Python) is missing."""


class DocumentDoesNotExistException(BaseEscherGraphException):
  """The specified document does not exist in the graph."""


class DocumentAlreadyExistsException(BaseEscherGraphException):
  """The graph attempts to build for a document that already exists."""


class FileException(BaseEscherGraphException):
  """Provided filepath is not a file or the file does not exist."""
