from __future__ import annotations

import json
import math
import time
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from pydantic import ValidationError

from eschergraph.agents.jinja_helper import process_template
from eschergraph.builder.models import ProcessedFile
from eschergraph.config import TOPIC_EXTRACTION
from eschergraph.config import TOPIC_RELATIONS
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.community import Community
from eschergraph.graph.node import Node
from eschergraph.persistence.metadata import Metadata

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
def build_community_layer(
  graph: Graph, processed_file: ProcessedFile, num_nodes: int
) -> list[Node]:
  """Build the community layer in the graph.

  The community layer corresponds to the nodes at level 1 of the graph.

  Args:
    graph (Graph): The graph to build the community layer for.
    processed_file (ProcessedFile): The file to extract the main topics for as communities.
    num_nodes (int): The number of nodes that need to be matched to communities.

  Returns:
    list[Node]: A list of community nodes.
  """
  # Extract the main topics for the community nodes
  main_topics: list[MainTopic] = _extract_main_topics(
    graph, full_text=processed_file.full_text, num_nodes=num_nodes
  )

  # Extract the relations between the main topics
  topics_relations: list[TopicRelations] = _extract_topic_relations(
    graph, main_topics=main_topics, full_text=processed_file.full_text
  )

  # Convert the main topics and topic relations into nodes and edges on the graph
  comm_nodes: list[Node] = _add_nodes_edges_to_graph(
    graph,
    main_topics=main_topics,
    topics_relations=topics_relations,
    document_id=processed_file.document.id,
  )

  # Match the level 0 nodes to a topic / community node
  level_0_nodes: list[Node] = graph.repository.get_all_at_level(
    level=0, document_id=processed_file.document.id
  )
  topic_node_str: list[str] = [
    node.name + ", " + node.description for node in comm_nodes
  ]
  num_reranker_requests: int = 0
  for node in level_0_nodes:
    if num_reranker_requests > 50:
      print("Sleeping for 30 seconds to avoid Jina rate limits")
      time.sleep(30)
      num_reranker_requests -= 25

    parent_node: Node = _match_closest_topic_node(
      graph, topic_nodes=comm_nodes, topic_nodes_text=topic_node_str, node=node
    )
    num_reranker_requests += 1
    node.community = Community(node=parent_node)
    parent_node.child_nodes.append(node)

  # Persist all the changes to the repository
  for node in level_0_nodes:
    graph.repository.add(node)

  for node in comm_nodes:
    graph.repository.add(node)

  return comm_nodes


def _extract_main_topics(
  graph: Graph, full_text: str, num_nodes: int
) -> list[MainTopic]:
  # Calculate the number of main topics that should be extracted
  # Prevent a community layer from having more nodes than level 0
  topic_lower: int = min(num_nodes // 4, 10)
  topic_upper: int = min(math.ceil(num_nodes / 3), 15)
  formatted_prompt: str = process_template(
    TOPIC_EXTRACTION,
    data={
      "full_text": full_text,
      "topic_lower": topic_lower,
      "topic_upper": topic_upper,
    },
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


def _add_nodes_edges_to_graph(
  graph: Graph,
  main_topics: list[MainTopic],
  topics_relations: list[TopicRelations],
  document_id: UUID,
) -> list[Node]:
  topic_nodes_name: dict[str, Node] = {}
  for topic in main_topics:
    topic_node: Node = graph.add_node(
      name=topic.name,
      description=topic.description,
      level=1,
      metadata=Metadata(document_id=document_id),
    )

    # Add the significance as a property to the topic node
    topic_node.add_property(
      description=topic.significance, metadata=Metadata(document_id=document_id)
    )

    topic_nodes_name[topic.name] = topic_node

  # Add all the edges to the community layer
  for topic_relations in topics_relations:
    frm_topic: Node = topic_nodes_name[topic_relations.name]
    for to_relation in topic_relations.relations:
      to_topic: Node = topic_nodes_name[to_relation.name]
      graph.add_edge(
        frm=frm_topic,
        to=to_topic,
        description=to_relation.description,
        metadata=Metadata(document_id=document_id),
      )

  return list(topic_nodes_name.values())


def _match_closest_topic_node(
  graph: Graph, topic_nodes_text: list[str], topic_nodes: list[Node], node: Node
) -> Node:
  node_str: str = node.name + ", " + node.description

  # Use the reranker to find the most similar topic node
  return topic_nodes[
    graph.reranker.rerank(query=node_str, text_list=topic_nodes_text, top_n=1)[0].index
  ]
