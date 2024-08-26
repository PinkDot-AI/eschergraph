from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

from fuzzywuzzy import fuzz


class FuzzyMatcher:
  """Matching node names based on Levenshtein distance."""

  @staticmethod
  def get_match_sets(names: list[str]) -> list[set[str]]:
    """Get the sets of matches for the provided names.

    Args:
      names (list[str]): The list of names.

    Returns:
      A list of sets of strings.

    """
    matches: dict[str, list[str]] = FuzzyMatcher._match_nodes(names)
    return FuzzyMatcher._match_sets(matches)

  @staticmethod
  def _match_nodes(node_names: list[str]) -> dict[str, list[str]]:
    """Matches nodes in a graph based on similarity to provided node names.

    :param graph: The graph containing nodes to be matched.
    :param node_names: A list of node names to be matched against the graph.
    :return: A dictionary where keys are node names and values are lists of matching nodes.
    """
    result: dict[str, list[str]] = dict()

    with ThreadPoolExecutor(max_workers=10) as executor:
      futures = [
        executor.submit(FuzzyMatcher._find_matches, name, node_names)
        for name in node_names
      ]
      for future in as_completed(futures):
        name, match_nodes = future.result()
        if match_nodes:
          result[name] = match_nodes
    return result

  @staticmethod
  def _is_similar(name1: str, name2: str) -> bool:
    """Checks if two node names are sufficiently similar using fuzzy matching.

    Args:
      name1 (str): The first name.
      name2 (str): The second name.

    Returns:
      True if sufficiently similar, False otherwise.
    """
    return bool(fuzz.token_set_ratio(name1, name2) >= 95)

  @staticmethod
  def _find_matches(query: str, names: list[str]) -> tuple[str, list[str]]:
    """Finds matches for a given query string within a list of names.

    Args:
      query (str): The query string to find matches for.
      names (list[str]): A list of node names to match against.

    Returns:
      A tuple where the first element is the query string
      and the second is a list of matching node names.
    """
    matches = []
    for name in names:
      if FuzzyMatcher._is_similar(query, name) and query != name:
        matches.append(name)
    return query, matches

  @staticmethod
  def _match_sets(matches: dict[str, list[str]]) -> list[set[str]]:
    """Group similar nodes into sets based on matching provided.

    Args:
      matches (dict[str, list[str]]): A dictionary that contains the list of matches
        under each node name.

    Returns:
      A list of sets, where each set contains names of similar nodes.
    """
    nodes_visited: set[str] = set()
    merged: list[set[str]] = []

    for key in matches.keys():
      if key in nodes_visited:
        continue
      cluster = FuzzyMatcher._vertical_matching(
        nodes_visited=nodes_visited,
        cluster={key},
        matches={k: set(v) for k, v in matches.items()},
        current=key,
      )
      merged.append(cluster)

    return merged

  @staticmethod
  def _vertical_matching(
    nodes_visited: set[str],
    cluster: set[str],
    matches: dict[str, set[str]],
    current: str,
  ) -> set[str]:
    """Recursively matches nodes to form clusters of similar nodes.

    Args:
      nodes_visited (set[str]): Set with visited node names.
      cluster (set[str]): Set with all (recursively) matched nodes.
      matches (dict[str, list[str]]): All fuzzy matches for each node.
      current (str): Name of the current node.

    Returns:
      The cluster of similar nodes as a set.
    """
    nodes_visited.add(current)

    for match in matches[current]:
      if match not in nodes_visited:
        cluster.add(match)
        cluster = FuzzyMatcher._vertical_matching(
          nodes_visited, cluster, matches, match
        )
    return cluster
