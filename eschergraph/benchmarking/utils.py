from __future__ import annotations

import json
from typing import Any


def save(data: dict[str, Any], filename: str) -> None:
  """Save a JSON object to file.

  data (dict[str, Any]): The data to save to a file in JSON format.
  filename (str): The save location.
  """
  with open(filename, "w") as file:
    json.dump(data, file, indent=4)


def load(filename: str) -> dict[str, Any]:
  """Load a JSON object to a dictionary.

  filename (str): The name of the file to load as a dictionary.

  Returns:
    The loaded data as a Python dictionary.
  """
  with open(filename, "r") as file:
    data: dict[str, Any] = json.load(file)
  return data
