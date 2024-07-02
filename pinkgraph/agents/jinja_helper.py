from __future__ import annotations

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
