from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import cast
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import NodeEdgeExt
from eschergraph.config import JSON_BUILD
from eschergraph.config import JSON_PROPERTY
from eschergraph.graph.persistence import Metadata
from eschergraph.tools.community_builder import CommunityBuilder
from eschergraph.tools.node_matcher import NodeMatcher
from eschergraph.tools.reader import Chunk

if TYPE_CHECKING:
  from eschergraph.graph.graph import Graph
  from eschergraph.graph.node import Node


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

    # Step 4: remove unmatched nodes from the updated logs

    # add persistence of new and old building logs
    self._persist_to_graph(graph=graph, updated_logs=updated_logs)

    # Build the community layer
    CommunityBuilder.build(level=0, graph=graph)

    # Adding changes to vector db
    graph.sync_vectordb()

    # self._save_logs()

    # Save graph (perhaps make explicit)
    graph.repository.save()

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

  def _persist_to_graph(self, graph: Graph, updated_logs: list[BuildLog]) -> None:
    # first add all nodes
    for log in updated_logs:
      for node_ext in log.nodes:
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
        frm: Node | None = graph.repository.get_node_by_name(
          edge_ext["source"].lower(), document_id=log.metadata.document_id
        )
        to: Node | None = graph.repository.get_node_by_name(
          edge_ext["target"].lower(), document_id=log.metadata.document_id
        )
        if not frm or not to:
          print("source or target node does not exist in nodes of this edge:", edge_ext)
          continue
        if frm == to:
          print(
            "tried to make an edge between 2 the same nodes, but added it as a property to the node."
          )
          frm.add_property(description=edge_ext["relationship"], metadata=log.metadata)
          continue
        graph.add_edge(
          frm=frm,
          to=to,
          description=edge_ext["relationship"],
          metadata=log.metadata,
        )

      # adding properties
      for prop_ext in log.properties:
        node: Node | None = graph.repository.get_node_by_name(
          prop_ext["entity_name"].lower(), document_id=log.metadata.document_id
        )
        if not node:
          print("node does not exsist", prop_ext["entity_name"].lower())
          continue
        for property_item in prop_ext["properties"]:
          node.add_property(description=property_item, metadata=log.metadata)
