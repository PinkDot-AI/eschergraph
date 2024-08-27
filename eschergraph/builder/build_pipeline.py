from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import cast

from attrs import define
from attrs import field

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeEdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.graph import Graph
from eschergraph.graph.node import Node
from eschergraph.graph.persistence import Metadata
from eschergraph.tools.node_matcher import NodeMatcher
from eschergraph.tools.reader import Chunk

JSON_BUILD = "json_build.jinja"
JSON_PROPERTY = "json_property.jinja"


@define
class BuildPipeline:
  """The build pipeline that converts chunks into objects to add to the graph."""

  model: ModelProvider
  reranker: Reranker
  building_logs: list[BuildLog] = field(factory=list)
  unique_entities: list[str] = field(factory=list)

  # TODO: copy the building logs somewhere
  def run(self, chunks: list[Chunk], graph: Graph) -> list[BuildLog]:
    """Run the build pipeline.

    Returns:
      A list of build logs that can be used to add nodes and edges to the graph.
    """
    # Step 1: extract the nodes and edges per chunk
    self._extract_node_edges(chunks)

    # Step 2: extract the properties per chunk (for extracted nodes)
    self._extract_properties()

    # Step 3: match the nodes together to extract entities from names
    unique_entities: list[str] = self._get_unique_entities()

    updated_logs: list[BuildLog] = NodeMatcher(
      model=self.model, reranker=self.reranker
    ).match(
      building_logs=self.building_logs,
      unique_node_names=unique_entities,
    )

    # TODO: add this step
    # Step 4: remove unmatched nodes from the updated logs

    # add persistence of new and old building logs
    self._persist_to_graph(graph=graph, updated_logs=updated_logs)

    # # adding changes to vector db
    graph.sync_vectordb()

    # # TODO build upperlayer
    # self._save_logs()

    return updated_logs

  def _extract_node_edges(self, chunks: list[Chunk]) -> None:
    with ThreadPoolExecutor(max_workers=self.model.max_threads) as executor:
      futures = {
        executor.submit(self._handle_nodes_edges_chunk, chunk) for chunk in chunks
      }
      for future in as_completed(futures):
        # TODO: add more exception handling
        try:
          future.result()
        except Exception as e:
          print(f"Error processing chunk: {e}")

  def _handle_nodes_edges_chunk(self, chunk: Chunk) -> None:
    prompt_formatted: str = process_template(JSON_BUILD, {"input_text": chunk.text})

    answer = self.model.get_json_response(prompt=prompt_formatted)
    json_nodes_edges: NodeEdgeExt = cast(NodeEdgeExt, answer)
    metadata: Metadata = Metadata(document_id=chunk.doc_id, chunk_id=chunk.chunk_id)

    # Add to the building logs
    self.building_logs.append(
      BuildLog(
        chunk_text=chunk.text,
        metadata=metadata,
        nodes=json_nodes_edges["entities"],
        edges=json_nodes_edges["relationships"],
      )
    )

  def _extract_properties(self) -> None:
    with ThreadPoolExecutor(max_workers=10) as executor:
      futures = {
        executor.submit(self._handle_property_chunk, log) for log in self.building_logs
      }
      # TODO: add more exception handling
      for future in as_completed(futures):
        try:
          future.result()
        except Exception as e:
          print(f"Error processing property: {e}")

  def _handle_property_chunk(self, log: BuildLog) -> None:
    node_names: list[str] = [node["name"] for node in log.nodes]

    if not node_names:
      return

    prompt_formatted: str = process_template(
      JSON_PROPERTY,
      {
        "current_nodes": ", ".join(node_names),
        "input_text": log.chunk_text,
      },
    )
    properties: dict[str, list[dict[str, list[str]]]] = self.model.get_json_response(
      prompt=prompt_formatted
    )
    log.properties = [
      {
        "entity_name": list(entity_prop.keys())[0],
        "properties": list(entity_prop.values())[0],
      }
      for entity_prop in properties["entities"]
    ]

  def _get_unique_entities(self) -> list[str]:
    unique_entities: set[str] = set()

    # Iterate over each log item in building_logs
    for log in self.building_logs:
      # Collect all entities from the edges (source and target)
      for edge in log.edges:
        unique_entities.add(edge["source"].lower())
        unique_entities.add(edge["target"].lower())

      # Collect all entities from the nodes
      for entity in log.nodes:
        unique_entities.add(entity["name"].lower())

      # Collect all entities from the properties
      for entity_dict in log.properties:
        unique_entities.add(entity_dict["entity_name"].lower())

    return list(unique_entities)

  def _persist_to_graph(self, graph: Graph, updated_logs: list[BuildLog]):
    # first add all nodes
    for log in updated_logs:
      for node_ext in log.nodes:
        node_ext: NodeExt = node_ext
        if graph.repository.get_node_by_name(
          node_ext["name"].lower(), document_id=log.metadata.document_id
        ):
          continue
        graph.add_node(
          name=node_ext["name"].lower(),
          description=node_ext["description"],
          level=0,
          metadata=log.metadata,
        )

    # then loop again to add all edges and properties
    for log in updated_logs:
      # adding edges
      for edge_ext in log.edges:
        edge_ext: EdgeExt = edge_ext
        frm: Node | None = graph.repository.get_node_by_name(
          edge_ext["source"].lower(), document_id=log.metadata.document_id
        )
        to: Node | None = graph.repository.get_node_by_name(
          edge_ext["target"].lower(), document_id=log.metadata.document_id
        )
        if not frm or not to:
          print(
            "source or target node does not exisist in nodes of this edge:", edge_ext
          )
          continue
        if frm == to:
          print("cannot make an edge between 2 the same nodes", edge_ext)
          continue
        graph.add_edge(
          frm=frm,
          to=to,
          description=edge_ext["relationship"],
          metadata=log.metadata,
        )

      # adding properties
      for prop_ext in log.properties:
        prop_ext: PropertyExt = prop_ext
        node: Node | None = graph.repository.get_node_by_name(
          prop_ext["entity_name"].lower(), document_id=log.metadata.document_id
        )
        if not node:
          print("node does not exsist", prop_ext["entity_name"].lower())
          continue
        for property_item in prop_ext["properties"]:
          node.add_property(description=property_item, metadata=log.metadata)

  # TODO: re-add the cost and time indication
  # def _get_cost_indication(self) -> float:
  #   """Estimates the cost based on the number of tokens and the model used.

  #   The completion tokens are assumed to be equal to prompt tokens.

  #   Returns:
  #     The estimated cost of processing.
  #   """
  #   model = self.model.model.value
  #   total_tokens = self.reader.total_tokens

  #   # Initialize variables
  #   prompt_cost: float = 0.0
  #   completion_cost: float = 0.0

  #   # Assumed that completion tokens are equal to prompt tokens
  #   if model == "gpt-4o":
  #     prompt_cost = (total_tokens / 1e6) * 5.00
  #     completion_cost = (total_tokens / 1e6) * 15.00
  #   elif model == "gpt-4o-mini":
  #     prompt_cost = (total_tokens / 1e6) * 0.150
  #     completion_cost = (total_tokens / 1e6) * 0.600
  #   else:
  #     raise ExternalProviderException("Invalid model specified.")

  #   total_cost: float = prompt_cost + completion_cost / 3
  #   return round(total_cost, 3)

  # def _get_time_indication(self) -> str:
  #   """Estimates the time required to process the document based on the number of chunks, the model used, and the number of parallel workers.

  #   Returns:
  #       float: The estimated time to complete the processing.
  #   """
  #   average_time_per_chunk: int = 0
  #   if self.model.model.value == "gpt-4o":
  #     average_time_per_chunk = 4  # seconds
  #   else:
  #     average_time_per_chunk = 2  # seconds

  #   num_chunks: int = len(self.reader.chunks)
  #   max_workers: int = 10  # as used in ThreadPoolExecutor

  #   # If number of chunks is less than or equal to max_workers,
  #   # the time taken would be approximately the time for one chunk.
  #   if num_chunks <= max_workers:
  #     estimated_time = average_time_per_chunk
  #   else:
  #     # Calculate the time for full batches and any remaining chunks
  #     full_batches = num_chunks // max_workers
  #     remaining_chunks = num_chunks % max_workers

  #     estimated_time = full_batches * average_time_per_chunk
  #     if remaining_chunks > 0:
  #       estimated_time += average_time_per_chunk

  #   # If the estimated time is more than 60 seconds, return time in minutes
  #   if estimated_time > 60:
  #     minutes = round(estimated_time // 60, 3)
  #     return f"{minutes} minute{'s' if minutes > 1 else ''}"
  #   else:
  #     return f"{round(estimated_time, 3)} seconds"
