from __future__ import annotations

import re
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape
from jinja2 import Template


def process_template(template_file: str, data: dict[str, str]) -> str:
  """Process the jinja template into a string.

  Function has been copied from: https://github.com/ArjanCodes/examples/blob/main/2024/tuesday_tips/jinja2/jinja_helper.py

  Args:
    template_file (str): The name of the jinja prompt template.
    data (dict): The parameters and their values to insert into the prompt.

  Returns:
    The formatted prompt as a string.
  """
  jinja_env = Environment(
    loader=FileSystemLoader(searchpath="./pinkgraph/agents/prompts"),
    autoescape=select_autoescape(),
  )
  template: Template = jinja_env.get_template(template_file)
  return template.render(**data)


def extract_variables(template_string: str) -> list[Any]:
  """Extract all variables in a Jinja template in string format.

  Args:
    template_string (str): the jinja template as a string.

  Returns:
    A list of all the identified variables in the string template.
  """
  variable_pattern: str = r"\{\{ *([\w_]+) *\}\}"
  return re.findall(variable_pattern, template_string)
