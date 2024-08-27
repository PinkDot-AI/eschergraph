from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from attrs import define

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.agents.reranker import RerankerResult
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.tools.fuzzy_matcher import FuzzyMatcher

JSON_UNIQUE_NODES = "identifying_nodes.jinja"


@define
class NodeMatcher:
  """This is the class for matching nodes that refer to the same entity."""

  model: ModelProvider
  reranker: Reranker

  def match(
    self,
    building_logs: list[BuildLog],
    unique_node_names: list[str],
  ) -> list[BuildLog]:
    """Match nodes that refer to the same entity together.

    Args:
        building_logs (list[BuildLog]): A list of building logs.
        unique_node_names (list[str]): A list of unique node names as extracted.

    Returns:
        list[BuildLog]: An updated list of build logs that can be used to add nodes and edges to the graph.
    """
    suggested_matches: list[set[str]] = FuzzyMatcher.get_match_sets(unique_node_names)
    updated_building_logs: list[BuildLog] = self.handle_merge(
      building_logs, suggested_matches
    )
    return updated_building_logs

  def _get_unique_nodes_gpt(self, suggested_match: set[str]) -> Any:
    """Create a prompt using the template and matches, then send it to GPT for a JSON response.

    Args:
        suggested_match (set[str]): A set of strings representing the entities to be included in the prompt.

    Returns:
        Any: The JSON response from the GPT model.
    """
    prompt: str = process_template(
      template_file=JSON_UNIQUE_NODES, data={"entities": ", ".join(suggested_match)}
    )
    response: Any = self.model.get_json_response(prompt=prompt)
    return response

  def _get_unique_nodes(self, suggested_matches: list[set[str]]) -> list[Any]:
    """Process suggested matches in parallel with 10 threads, send each to GPT, and collect JSON responses.

    Args:
        suggested_matches (list[set[str]]): A list of sets, where each set contains strings representing entities to be included in a prompt.

    Returns:
        list[Any]: A list of JSON responses from the GPT model for each set of suggested matches.
    """

    def process_single_match(suggested_match: set[str]) -> Any:
      return self._get_unique_nodes_gpt(suggested_match)

    with ThreadPoolExecutor(max_workers=10) as executor:
      results = list(executor.map(process_single_match, suggested_matches))

    return results

  def _assign_node(self, description: str, node_info: dict[str, list[str]]) -> str:
    """Assigns the most appropriate node based on description and node information.

    Args:
        description (str): The description used for assignment.
        node_info (dict[str, list[str]]): A dictionary containing node information.

    Returns:
        str: The assigned node name.
    """
    docs = [
      f"{entity}---{' '.join(descriptions)}"
      for entity, descriptions in node_info.items()
    ]

    top_result: list[RerankerResult] | None = self.reranker.rerank(
      query=description, text_list=docs, top_n=1
    )
    if not top_result:
      print("There was an error with the reranker in the merging function")
      return next(iter(node_info))
    return top_result[0].text.split("---")[0]

  def _collect_node_info(
    self, build_log: list[BuildLog], nodes: list[str]
  ) -> dict[str, list[str]]:
    """Collects information about nodes from build logs.

    Args:
        build_log (list[BuildLog]): The build logs to extract information from.
        nodes (list[str]): The list of node names to collect information for.

    Returns:
        dict[str, list[str]]: A dictionary mapping node names to their collected information.
    """
    node_info: dict[str, list[str]] = {node: [] for node in nodes}

    for log in build_log:
      for entity in log.nodes:
        name = entity.get("name", "").lower()
        for node in nodes:
          if node in name:
            node_info[node].append(entity.get("description", ""))

      for edge in log.edges:
        source = edge.get("source", "").lower()
        target = edge.get("target", "").lower()
        for node in nodes:
          if node in source or node in target:
            description = edge.get("relationship", "")
            if isinstance(description, str):
              node_info[node].append(description)

      if log.properties:
        log_properties: list[PropertyExt] = log.properties
        for prop_item in log_properties:
          entity_name_lower = prop_item["entity_name"].lower()
          if entity_name_lower in nodes:
            if isinstance(prop_item["properties"], list):
              for property in prop_item["properties"]:
                node_info[entity_name_lower].append(property)

    return node_info

  def handle_merge(
    self, building_logs: list[BuildLog], suggested_matches: list[set[str]]
  ) -> list[BuildLog]:
    """Handle merging of entities based on suggested matches.

    Args:
        building_logs (list[BuildLog]): The build logs to process.
        suggested_matches (list[set[str]]): The suggested matches for merging.

    Returns:
        list[BuildLog]: The updated build logs after merging.
    """
    gpt_identified_matches: list[Any] = self._get_unique_nodes(suggested_matches)

    for identified_matches, suggestion in zip(
      gpt_identified_matches, suggested_matches
    ):
      true_nodes, entity_to_nodes = self._build_entity_to_nodes_map(identified_matches)

      if set(entity_to_nodes.keys()) != suggestion:
        print("LLM extraction error", set(entity_to_nodes.keys()))
        print("suggestions", suggestion)

      if true_nodes == suggestion:
        print(
          "No need for any merging because Levenshtein suggestion is the same as the GPT suggestion"
        )
        continue

      self._process_entities_for_logs(building_logs, entity_to_nodes)

    return building_logs

  def _build_entity_to_nodes_map(
    self, identified_matches: Any
  ) -> tuple[set[str], dict[str, set[str]]]:
    """Build a mapping of merged entities to the true nodes they appear in.

    Args:
        identified_matches (Any): The matches identified by GPT.

    Returns:
        tuple[set[str], dict[str, set[str]]]: A set of true nodes and a mapping from entities to nodes.
    """
    true_nodes = {entity["name"].lower() for entity in identified_matches["entities"]}
    entity_to_nodes: dict[str, set[str]] = {}

    for entity in identified_matches["entities"]:
      node_name = entity["name"].lower()
      for merged_entity in entity["merged entities"]:
        entity_to_nodes.setdefault(merged_entity.lower(), set()).add(node_name)

    return true_nodes, entity_to_nodes

  def _process_entities_for_logs(
    self, building_logs: list[BuildLog], entity_to_nodes: dict[str, set[str]]
  ) -> None:
    """Process each entity and update the logs with the correct merged entities.

    Args:
        building_logs (list[BuildLog]): The build logs to update.
        entity_to_nodes (dict[str, set[str]]): The mapping from entities to nodes.
    """
    for entity, nodes in entity_to_nodes.items():
      if len(nodes) == 0:
        print(f"Something is going wrong, check the logging for entity: {entity}")
        continue

      if len(nodes) == 1:
        true_node = next(iter(nodes))
        if entity == true_node:
          continue
        print(f'Merging "{entity}" into true entity "{true_node}"')

      node_info = self._collect_node_info(building_logs, list(nodes))
      assigned_node_cache: dict[str, str] = {}

      for log_item in building_logs:
        self._update_log_item(log_item, entity, node_info, assigned_node_cache)

  def _update_log_item(
    self,
    log: BuildLog,
    entity: str,
    node_info: dict[str, list[str]],
    assigned_node_cache: dict[str, str],
  ) -> None:
    """Update a single log item with the correct entity names.

    Args:
        log (BuildLog): The log item to update.
        entity (str): The entity name to replace.
        node_info (dict[str, list[str]]): The node information for assignment.
        assigned_node_cache (dict[str, str]): A cache to store assigned nodes.
    """
    assigned_node_cache = {}

    for entity_item in log.nodes:
      self._replace_entity_name(
        entity_item, "name", entity, node_info, assigned_node_cache
      )

    for relationship_item in log.edges:
      for role in ["source", "target"]:
        self._replace_entity_name(
          relationship_item, role, entity, node_info, assigned_node_cache
        )

    if log.properties:
      for prop_item in log.properties:
        prop_item: PropertyExt = prop_item
        node_name_lower = prop_item["entity_name"].lower()
        if entity == node_name_lower:
          if entity not in assigned_node_cache:
            assigned_node_cache[entity] = self._assign_node(
              description=node_name_lower, node_info=node_info
            )
          assigned_node = assigned_node_cache[entity]
          print(
            f'Replacing property key "{node_name_lower}" with "{assigned_node}" in properties_json.'
          )
          prop_item["entity_name"] = assigned_node.lower()

  def _replace_entity_name(
    self,
    item: NodeExt | EdgeExt,
    key: str,
    entity: str,
    node_info: dict[str, list[str]],
    assigned_node_cache: dict[str, str],
  ) -> None:
    """Replace entity name in the given item.

    Args:
        item (NodeExt | EdgeExt): The item to update.
        key (str): The key in the item to replace.
        entity (str): The entity name to replace.
        node_info (dict[str, list[str]]): The node information for assignment.
        assigned_node_cache (dict[str, str]): A cache to store assigned nodes.
    """
    entity_name = item[key].lower()
    if entity_name == entity:
      if entity_name not in assigned_node_cache:
        description = item[key] + ", " + item.get("description", "")
        assigned_node_cache[entity_name] = self._assign_node(
          description=description, node_info=node_info
        )
      assigned_node = assigned_node_cache[entity_name]
      print(
        f'Replacing {key} "{entity}" with "{assigned_node}" in item {(entity_name, item.get("description", ""))}.'
      )
      item[key] = assigned_node
