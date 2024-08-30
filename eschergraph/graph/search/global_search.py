from __future__ import annotations

import concurrent.futures
import json
from typing import cast
from typing import List
from typing import Optional
from typing import TYPE_CHECKING
from uuid import UUID

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.node import Node
from eschergraph.graph.property import Property

if TYPE_CHECKING:
  from eschergraph.graph import Graph


def global_search(
  graph: Graph, prompt: str, collection_name: str = "main_collection"
) -> str | None:
  """Search a graph globally through it's communities.

  Note that the findings for a community should be sorted, this is the default behavior when building a graph.

  Args:
    graph (Graph): A graph object
    prompt (str): The question to answer
    collection_name (str): The collection of the vector database to use
  """
  extracted_nodes = extract_entities_from(prompt, graph.model)
  ans_template = "search/question_with_context.jinja"
  if len(extracted_nodes) > 0:
    props = retrieve_similar_properties(
      graph=graph, prompt=prompt, collection_name=collection_name
    )
  else:
    props: list[Property] = retrieve_key_properties(graph)
  context = "\n".join([prop.description for prop in props])
  full_prompt = process_template(ans_template, {"CONTEXT": context, "QUERY": prompt})
  return graph.model.get_plain_response(full_prompt)


def retrieve_similar_properties(
  graph: Graph,
  prompt: str,
  collection_name: str,
  levels_to_search: int = 3,
  properties_to_return: int = 10,
  top_vec_results: int = 5,
  top_node_properties: int = 3,
) -> List[Property]:
  """A search of the graph based on the similarity of prompt and nodes.

  Args:
    graph (Graph): Graph object
    prompt (str): Question or statement to be searched for in the graph
    collection_name (str): The collection of the vector database to use
    levels_to_search (int): How many graph levels to search from the max. Defaults to 3.
    properties_to_return (int): Maximum properties to return. Defaults to 10.
    top_vec_results (int): Maximum nodes to be used per level. Defaults to 5.
    top_node_properties (int): Maximum properties to use per node. Defaults to 3.

  Returns:
    List[Property]: A list of properties
  """
  # Search is done from top level
  curr_level = graph.repository.get_max_level()
  stop_level = max(curr_level - levels_to_search, 0)

  search_res: List[Node | None] = []
  while curr_level >= stop_level:
    res = graph.vector_db.format_search_results(
      graph.vector_db.search(
        query=prompt,
        top_n=top_vec_results,
        metadata={"level": curr_level},
        collection_name=collection_name,
      ),
    )
    search_res.extend([
      graph.repository.get_node_by_id(cast(UUID, nd["id"])) for nd in res
    ])
    curr_level -= 1
  props = [
    prop
    for nd in search_res
    if nd is not None and nd.properties
    for prop in nd.properties[:top_node_properties]
  ]
  rank_res = graph.reranker.rerank(
    prompt, [fd.description for fd in props], properties_to_return
  )
  return [props[ranked.index] for ranked in rank_res if ranked.index < len(props)]


def retrieve_key_properties(
  graph: Graph,
  n: int = 2,
  sorted: bool = True,
  level: Optional[int] = None,
) -> List[Property]:
  """Retrieve most important properties of a level.

  Args:
    graph (Graph): A graph with at least a depth of _level_
    n (int): Top properties to retrieve per node. Defaults to 2.
    sorted (bool): Sort the findings in nodes on impact/importance if this has not been done yet at graph creation. Defaults to True.
    level (Optional[int]): Specify specific node level other than max level.

  Returns:
    List[Property]: A list of properties
  """
  node_level = level if level is not None else graph.repository.get_max_level()
  nodes = graph.repository.get_all_at_level(node_level)
  # Properties of reports should be sorted when building the graph
  if sorted:
    key_props = [prop for nd in nodes if nd.properties for prop in nd.properties[:n]]
  else:
    with concurrent.futures.ThreadPoolExecutor(
      max_workers=graph.model.max_threads
    ) as executor:
      props_per_node = list(
        executor.map(lambda nd: order_properties(nd, llm=graph.model), nodes)
      )
    key_props = [prop for props in props_per_node for prop in props[:n]]
  return key_props


def order_properties(nd: Node, llm: ModelProvider) -> List[Property]:
  """Order the properties of a node.

  Args:
    nd (Node): The node of which to order the properties
    llm (ModelProvider): The llm with which to order the properties
  Returns:
    Dict[str, List[dict]]: a dict with ordered properties
  """
  template = "search/importance_rank.jinja"
  jsonized = json.dumps(
    [{"explanation": prop.description} for prop in nd.properties], indent=4
  )
  prompt = process_template(template, {"json_list": jsonized})
  output = llm.get_json_response(prompt=prompt)
  if output is None:
    raise ExternalProviderException("Empty message response from formatted response")
  if not isinstance(output, list):
    raise ExternalProviderException("Non-list response from LLM")
  # Clear out old properties
  nd.properties = []
  return [Property.create(nd, description=prop["explanation"]) for prop in output]


def extract_entities_from(query: str, llm: ModelProvider) -> List[str]:
  """Extract entities from query.

  Args:
      query (str): Text
      llm (ModelProvider): A large language ModelProvider class
  Returns:
      List[str]: list of entities
  """
  entity_extraction_template = "search/entity_extraction.jinja"
  prompt = process_template(
    entity_extraction_template,
    {"query": query},
  )
  res = llm.get_json_response(prompt=prompt)
  if not res:
    raise ExternalProviderException("Empty message response while extracting entities")
  try:
    return res["entities"]
  except:
    raise ExternalProviderException("jsonify failed at extracting entities from query")
