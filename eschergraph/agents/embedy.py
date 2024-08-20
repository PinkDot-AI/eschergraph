from abc import ABC, abstractmethod
from typing import List


class Embed(ABC):
  """The abstract base class for embedders used in the package."""

  @abstractmethod
  def embed(inputs: List[str]) -> List[List[float]]:
    """Embed all input strings as vector.

    Args:
        inputs (List[str]): A list of string inputs

    Returns:
        List[List[float]]: A list of vector outputs
    """
    ...
