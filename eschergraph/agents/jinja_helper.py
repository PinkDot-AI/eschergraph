from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape
from jinja2 import Template

from eschergraph.exceptions import PromptFormattingException


def process_template(template_file: str, data: dict[str, str]) -> str:
  """Process the jinja template into a string.

  Function has been inspired by: https://github.com/ArjanCodes/examples/blob/main/2024/tuesday_tips/jinja2/jinja_helper.py

  Args:
    template_file (str): The name of the jinja prompt template.
    data (dict): The parameters and their values to insert into the prompt.

  Returns:
    The formatted prompt as a string.
  """
  parent_path: str = Path(__file__).parent.absolute().as_posix()
  jinja_env: Environment = Environment(
    loader=FileSystemLoader(searchpath=parent_path + "/prompts"),
    autoescape=select_autoescape(),
  )

  template_variables: list[Any] = extract_variables(template_file, jinja_env)

  # Check if all variables in template have been provided as data
  if not set(template_variables) == set(data.keys()):
    raise PromptFormattingException(
      "Some variables in the prompt have not been formatted."
    )

  template: Template = jinja_env.get_template(template_file)

  return template.render(**data)


def extract_variables(template_file: str, jinja_env: Environment) -> list[Any]:
  """Extract all variables in a Jinja template in string format.

  Args:
    template_file (str): the name of the jinja prompt template.
    jinja_env (Environment): the jinja Environment.

  Returns:
    A list of all the identified variables in the string template.
  """
  # Check if the baseloader is None
  if not jinja_env.loader:
    raise PromptFormattingException(
      "Something went wrong formatting the prompt template."
    )
  else:
    loader: BaseLoader = jinja_env.loader

  # Get the template as plain text
  plain_template: str = loader.get_source(jinja_env, template_file)[0]

  variable_pattern: str = r"\{\{ *([\w_]+) *\}\}"
  return re.findall(variable_pattern, plain_template)
