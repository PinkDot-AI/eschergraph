from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ValidationError

from eschergraph.agents.jinja_helper import process_template
from eschergraph.builder.models import ProcessedFile
from eschergraph.config import TOPIC_EXTRACTION
from eschergraph.config import TOPIC_RELATIONS
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.node import Node

if TYPE_CHECKING:
  from eschergraph.graph import Graph


# Pydantic models used to validate the JSON responses from the model
class MainTopic(BaseModel):
  """A main topic as extracted by the model."""

  name: str
  description: str
  significance: str


class Relation(BaseModel):
  """A relation that is attached to a topic."""

  name: str
  description: str


class TopicRelations(BaseModel):
  """The relations grouped per topic."""

  name: str
  relations: list[Relation]


# TODO: add the community building as a purely functional module
def build_community_layer(graph: Graph, processed_file: ProcessedFile) -> list[Node]:
  """Build the community layer in the graph.

  The community layer corresponds to the nodes at level 1 of the graph.

  Args:
    graph (Graph): The graph to build the community layer for.
    processed_file (ProcessedFile): The file to extract the main topics for as communities.

  Returns:
    list[Node]: A list of community nodes.
  """
  ...


def _extract_main_topics(graph: Graph, full_text: str) -> list[MainTopic]:
  formatted_prompt: str = process_template(
    TOPIC_EXTRACTION, data={"full_text": full_text}
  )
  try:
    return [
      MainTopic(**topic)
      for topic in graph.model.get_json_response(formatted_prompt)["topics"]
    ]
  except (KeyError, ValidationError):
    raise ExternalProviderException("Something went wrong parsing the main topics")


# TODO: consider adding a potential check for whether the topics and the topics with relations attached match
def _extract_topic_relations(
  graph: Graph, main_topics: list[MainTopic], full_text: str
) -> list[TopicRelations]:
  main_topics_str: str = json.dumps(
    [topic.model_dump() for topic in main_topics], indent=4
  )
  prompt_formatted: str = process_template(
    TOPIC_RELATIONS, data={"main_topics": main_topics_str, "full_text": full_text}
  )
  try:
    return [
      TopicRelations(**relation)
      for relation in graph.model.get_json_response(prompt_formatted)["relations"]
    ]
  except (KeyError, ValidationError):
    raise ExternalProviderException(
      "Something went wrong parsing the main topic relations"
    )
