from __future__ import annotations

import pytest
from assertpy import assert_that
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

from eschergraph.agents.jinja_helper import extract_variables
from eschergraph.agents.jinja_helper import process_template
from eschergraph.exceptions import PromptFormattingException

json_build_template: str = """-Goal-
Extract all relevant information from the provided text into a graph representation containing entities and relations.
The most important part is that you try to represent all the information in the provided text in a structured format!

-Steps-
1. Identify all named entities in singular form. For people please include the entire name. Entities can also be technologties.
For each identified entity, extract the following information:
- entity_name: Name of the entity
- entity_description: Comprehensive description of the entity's attributes and activities

Format each entity output as a JSON entry with the following format:

{"name": <entity name>, "description": <entity description>}

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other

Format each relationship as a JSON entry with the following format:

{"source": <source_entity>, "target": <target_entity>, "relationship": <relationship_description>}

3. Return output in English as a single list of all JSON entities and relationships identified in steps 1 and 2.
return the JSON like this:

{
 'entities': [{"name": <entity name1>, "description": <entity description1>}, {"name": <entity name1>, "description": <entity description1>}],
 'relationships':[{"source": <source_entity>, "target": <target_entity>, "relationship": <relationship_description>}, and more]
}

However, only extract entities that are specific so avoid extracting entities like CEO or employee, but instead
extract only named entities.

-Real Data-
######################
text: This is a test
######################
output:"""

input_text: str = "This is a test"


def test_templating_function_json_build() -> None:
  assert (
    process_template(template_file="json_build.jinja", data={"input_text": input_text})
    == json_build_template
  )


def test_templating_function_json_build_empty_data() -> None:
  with pytest.raises(PromptFormattingException):
    process_template(template_file="json_build.jinja", data={})


def test_templating_function_json_property_missing_data() -> None:
  with pytest.raises(PromptFormattingException):
    process_template(
      template_file="json_property.jinja", data={"input_text": input_text}
    )


def test_extract_variables() -> None:
  jinja_env: Environment = Environment(
    loader=FileSystemLoader(searchpath="./eschergraph/agents/prompts"),
    autoescape=select_autoescape(),
  )

  assert_that(
    extract_variables("json_property.jinja", jinja_env)
  ).does_not_contain_duplicates().contains_only("input_text", "current_nodes")
