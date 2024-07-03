from __future__ import annotations

import pytest
from assertpy import assert_that
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

from pinkgraph.agents.jinja_helper import extract_variables
from pinkgraph.agents.jinja_helper import process_template
from pinkgraph.exceptions import PromptFormattingException

property_template: str = """Add the properties as described in the execution plan to each of the entities exactly as listed.

The execution plan:
{execution_plan}

Add the listed properties to each node with a function call! Do not miss a single one!!
Lives may depend on it!!! Mistakes are extremely costly for me and my career!"""

elaboration_plan_template: str = """You need to expand the existing knowledge graph based on the new context that is provided.
It is your task to devise an extensive execution plan for doing this.

Please specify the following steps:
1. Extracting the entities
2. Indicating the importance of the entity in the provided text as: small, medium or large
3. Adding relevant properties to each of the entities
4. Identifying relationships between the entities

Especially the relationships between the entities are important, so take extra care in identifying these.
In addition, please specify these relationships in the following format.
- [ENTITY_1] -> [RELATIONSHIP] -> [ENTITY_2]

For example,
- [Tim Cook] -> [works at] -> [Apple]
- [Paris] -> [is located in] -> [France]
- [Google] -> [is headquartered in] -> [Mountain View, California]

The text: {context}
The current graph: {graph}"""

execution_plan: str = "Do nothing this is a test!"
graph: str = "This is the entire graph"
context: str = "A lot of useful context"


def test_templating_function_property() -> None:
  assert process_template(
    template_file="property.jinja", data={"execution_plan": execution_plan}
  ) == property_template.format(execution_plan=execution_plan)


def test_templating_function_elaboration_plan() -> None:
  assert process_template(
    template_file="elaboration_plan.jinja", data={"context": context, "graph": graph}
  ) == elaboration_plan_template.format(graph=graph, context=context)


def test_templating_function_property_empty_data() -> None:
  with pytest.raises(PromptFormattingException):
    process_template(template_file="property.jinja", data={})


def test_templating_function_elaboration_missing_data() -> None:
  with pytest.raises(PromptFormattingException):
    process_template(template_file="elaboration_plan.jinja", data={"graph": graph})


def test_extract_variables() -> None:
  jinja_env: Environment = Environment(
    loader=FileSystemLoader(searchpath="./pinkgraph/agents/prompts"),
    autoescape=select_autoescape(),
  )

  assert_that(
    extract_variables("elaboration_plan.jinja", jinja_env)
  ).does_not_contain_duplicates().contains_only("context", "graph")
