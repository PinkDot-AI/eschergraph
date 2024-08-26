from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from attrs import define
from fuzzywuzzy import fuzz

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.agents.reranker import RerankerResult
from eschergraph.builder.build_log import BuildLog
from eschergraph.tools.reader import Chunk

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
    chunks: list[Chunk],
  ) -> list[BuildLog]:
    """Match nodes that refer to the same entity together.

    Args:
      building_logs (list[BuildLog]): A list of building logs.
      unique_node_names (list[str]): A list of unique node names as extracted.
      chunks (list[Chunk]): All the chunks in the document.
    """
    matches: dict[str, list[str]] = self._match_nodes(unique_node_names)
    suggested_matches: list[set[str]] = self._match_sets(matches)
    updated_building_logs: list[BuildLog] = self.handle_merge(
      building_logs, suggested_matches
    )
    return updated_building_logs

  def _match_nodes(self, node_names: list[str]) -> dict[str, list[str]]:
    """Matches nodes in a graph based on similarity to provided node names.

    :param graph: The graph containing nodes to be matched.
    :param node_names: A list of node names to be matched against the graph.
    :return: A dictionary where keys are node names and values are lists of matching nodes.
    """
    result: dict[str, list[str]] = dict()

    with ThreadPoolExecutor() as executor:
      futures = {
        executor.submit(self._find_matches, name, node_names): name
        for name in node_names
      }
      for future in as_completed(futures):
        name, match_nodes = future.result()
        if match_nodes:
          result[name] = match_nodes
    return result

  @staticmethod
  def _is_similar(name1: str, name2: str) -> bool:
    """Checks if two node names are sufficiently similar using fuzzy matching.

    :param name1: The first node name.
    :param name2: The second node name.
    :return: True if the names are sufficiently similar, False otherwise.
    """
    similarity = fuzz.token_set_ratio(name1, name2)
    prediction: bool = similarity >= 95
    return prediction

  def _find_matches(self, query: str, names: list[str]) -> tuple[str, list[str]]:
    """Finds matches for a given query string within a list of names.

    :param query: The query string to find matches for.
    :param names: A list of node names to match against.
    :return: A tuple where the first element is the query string and the second is a list of matching node names.
    """
    matches = []
    for name in names:
      if self._is_similar(query, name) and query != name:
        matches.append(name)
    return query, matches

  def _match_sets(self, matches: dict[str, list[str]]) -> list[set[str]]:
    """Groups similar nodes into sets based on matching criteria.

    :param matches: A dictionary of node names and their matching nodes.
    :return: A list of sets, where each set contains names of similar nodes.
    """
    nodes_visited: set[str] = set()
    merged: list[set[str]] = []

    for key in matches.keys():
      if key in nodes_visited:
        continue
      cluster = self._vertical_matching(
        nodes_visited=nodes_visited,
        cluster={key},  # Rewritten to use a set literal
        matches={k: set(v) for k, v in matches.items()},  # Convert lists to sets
        current=key,
      )
      merged.append(cluster)

    return merged

  def _vertical_matching(
    self,
    nodes_visited: set[str],
    cluster: set[str],
    matches: dict[str, set[str]],
    current: str,
  ) -> set[str]:
    """Recursively matches nodes to form clusters of similar nodes.

    :param nodes_visited: A set of nodes that have already been visited.
    :param cluster: A set representing the current cluster of matched nodes.
    :param matches: A dictionary of node names and their matching nodes.
    :param current: The current node being processed.
    :return: A set containing all nodes in the current cluster.
    """
    nodes_visited.add(current)

    for match in matches[current]:
      if match not in nodes_visited:
        cluster.add(match)
        cluster = self._vertical_matching(nodes_visited, cluster, matches, match)
    return cluster

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
    response: Any = self.model.get_formatted_response(
      prompt=prompt, response_format={"type": "json_object"}
    )
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
    # Construct the docs list in a single list comprehension
    docs = [
      f"{entity}---{' '.join(descriptions)}"
      for entity, descriptions in node_info.items()
    ]

    # Use the reranker to find the top matching node
    top_result: list[RerankerResult] | None = self.reranker.rerank(
      query=description, texts_list=docs, top_n=1
    )
    if not top_result:
      print("There was an error with the reranker in the merging function")
      return next(iter(node_info))
    # Extract and return the entity name from the top result
    return top_result[0].text.split("---")[0]

  def _collect_node_info(
    self, build_log_items: list[BuildLog], nodes: list[str]
  ) -> dict[str, list[str]]:
    node_info: dict[str, list[str]] = {node: [] for node in nodes}

    for item in build_log_items:
      # Extracting data from node_edge_json
      for entity in item.node_edge_json.get("entities", []):
        name = entity.get("name", "").lower()
        for node in nodes:
          if node in name:
            node_info[node].append(entity.get("description", ""))

      # Extracting data from relationships in node_edge_json
      for relationship in item.node_edge_json.get("relationships", []):
        source = relationship.get("source", "").lower()
        target = relationship.get("target", "").lower()
        for node in nodes:
          if node in source or node in target:
            node_info[node].append(relationship.get("description", ""))

      # Extracting data from properties_json
      if item.properties_json:
        for entity_dict in item.properties_json["entities"]:
          for entity_name, property_list in entity_dict.items():
            entity_name_lower = entity_name.lower()
            if entity_name_lower in nodes:
              for property in property_list:
                node_info[entity_name_lower].extend(property)

    return node_info

  def handle_merge(
    self, building_logs: list[BuildLog], suggested_matches: list[set[str]]
  ) -> list[BuildLog]:
    """Handle merging of entities based on suggested matches."""
    gpt_identified_matches: list[Any] = self._get_unique_nodes(suggested_matches)

    for identified_matches, suggestion in zip(
      gpt_identified_matches, suggested_matches
    ):
      true_nodes, entity_to_nodes = self._build_entity_to_nodes_map(identified_matches)

      # Check for LLM extraction error
      if set(entity_to_nodes.keys()) != suggestion:
        print("LLM extraction error", set(entity_to_nodes.keys()))
        print("suggestions", suggestion)

      # If true nodes match the suggestion, no merge is needed
      if true_nodes == suggestion:
        print(
          "No need for any merging because levenstien suggestion is the same as the gpt suggestion"
        )
        continue

      self._process_entities_for_logs(building_logs, entity_to_nodes)

    return building_logs

  def _build_entity_to_nodes_map(
    self, identified_matches: Any
  ) -> tuple[set[str], dict[str, set[str]]]:
    """Build a mapping of merged entities to the true nodes they appear in."""
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
    """Process each entity and update the logs with the correct merged entities."""
    for entity, nodes in entity_to_nodes.items():
      if len(nodes) == 0:
        print(f"Something is going wrong, check the logging for entity: {entity}")
        continue

      if len(nodes) == 1:
        true_node = next(iter(nodes))
        if entity == true_node:
          # No need to merge these entities, they are already the same
          continue
        print(f'Merging "{entity}" into true entity "{true_node}"')

      node_info = self._collect_node_info(building_logs, list(nodes))
      assigned_node_cache: dict[str, str] = {}

      for log_item in building_logs:
        self._update_log_item(log_item, entity, node_info, assigned_node_cache)

  def _update_log_item(
    self,
    log_item: BuildLog,
    entity: str,
    node_info: dict[str, list[str]],
    assigned_node_cache: dict[str, str],
  ) -> None:
    """Update a single log item with the correct entity names."""
    node_edge_json = log_item.node_edge_json
    properties_json = log_item.properties_json

    # reset node cache
    assigned_node_cache = {}

    # Process node_edge_json entities
    for entity_item in node_edge_json.get("entities", []):
      self._replace_entity_name(
        entity_item, "name", entity, node_info, assigned_node_cache
      )

    # Process node_edge_json relationships
    for relationship_item in node_edge_json.get("relationships", []):
      for role in ["source", "target"]:
        self._replace_entity_name(
          relationship_item, role, entity, node_info, assigned_node_cache
        )

    # Process properties_json
    if properties_json:
      for entity_dict in properties_json["entities"]:
        # Iterate over keys in entity_dict
        for key in list(
          entity_dict.keys()
        ):  # Use list() to avoid issues with modifying the dictionary during iteration
          if entity == key.lower():  # Compare both in lowercase
            if entity not in assigned_node_cache:
              description = ", ".join(entity_dict[key])
              assigned_node_cache[entity] = self._assign_node(
                description=description, node_info=node_info
              )
            assigned_node = assigned_node_cache[entity]
            print(
              f'Replacing property key "{key}" with "{assigned_node}" in properties_json.'
            )
            # Replace the key with the assigned node
            entity_dict[assigned_node] = entity_dict.pop(key)

  def _replace_entity_name(
    self,
    item: dict[str, Any],
    key: str,
    entity: str,
    node_info: dict[str, list[str]],
    assigned_node_cache: dict[str, str],
  ) -> None:
    """Replace entity name in the given item."""
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
