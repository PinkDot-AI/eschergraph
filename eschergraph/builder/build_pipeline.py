from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import cast
from typing import TYPE_CHECKING
from uuid import uuid4

from attrs import define
from attrs import field

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.reranker import Reranker
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import NodeEdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.building_tools import BuildingTools
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.builder.reader.reader import Chunk
from eschergraph.config import JSON_BUILD
from eschergraph.config import JSON_FIGURE
from eschergraph.config import JSON_KEYWORDS
from eschergraph.config import JSON_PROPERTY
from eschergraph.config import JSON_TABLE
from eschergraph.exceptions import ImageProcessingException
from eschergraph.exceptions import NodeCreationException
from eschergraph.persistence.metadata import Metadata
from eschergraph.persistence.metadata import MetadataVisual
from eschergraph.tools.community_builder import CommunityBuilder
from eschergraph.tools.node_matcher import NodeMatcher

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
  keywords: list[str] = field(factory=list)

  def run(
    self,
    chunks: list[Chunk],
    graph: Graph,
    full_text: str,
    visual_elements: list[VisualDocumentElement] | None = None,
  ) -> list[BuildLog]:
    """Run the build pipeline.

    Returns:
      A list of build logs that can be used to add nodes and edges to the graph.
    """
    self._extract_keywords(full_text=full_text)

    self._extract_node_edges(chunks)

    self._extract_properties()

    if visual_elements:
      self._handle_multi_modal(visual_elements)

    unique_entities: list[str] = self._get_unique_entities()

    updated_logs: list[BuildLog] = NodeMatcher(
      model=self.model, reranker=self.reranker
    ).match(
      building_logs=self.building_logs,
      unique_node_names=unique_entities,
    )

    # Step 4: remove unmatched nodes from the updated logs
    self._persist_to_graph(graph=graph, updated_logs=updated_logs)

    CommunityBuilder.build(level=0, graph=graph)

    graph.sync_vectordb()

    # self._save_logs()

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

  def _extract_keywords(self, full_text: str) -> None:
    prompt_formatted: str = process_template(JSON_KEYWORDS, {"full_text": full_text})
    answer_json = self.model.get_json_response(prompt=prompt_formatted)
    try:
      self.keywords = answer_json["keywords"]
    except:
      raise NodeCreationException("keywords extraction not in correct format")

  def _handle_nodes_edges_chunk(self, chunk: Chunk) -> None:
    prompt_formatted: str = process_template(JSON_BUILD, {"input_text": chunk.text})

    answer = self.model.get_json_response(prompt=prompt_formatted)
    json_nodes_edges: NodeEdgeExt = cast(NodeEdgeExt, answer)
    metadata: Metadata = Metadata(
      document_id=chunk.doc_id, chunk_id=chunk.chunk_id, visual_metadata=None
    )

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
      if log.metadata.visual_metadata:
        # ship all visual items for node merging
        continue
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
      # add conditional is_visual to the node if the buildinglogs says so

      for node_ext in log.nodes:
        is_visual = (
          log.main_visual_entity_name
          and log.main_visual_entity_name.lower() == node_ext["name"].lower()
        )
        if graph.repository.get_node_by_name(
          node_ext["name"].lower(), document_id=log.metadata.document_id
        ):
          continue
        graph.add_node(
          name=node_ext["name"].lower(),
          description=node_ext["description"],
          level=0,
          metadata=log.metadata,
          is_visual=is_visual,
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
          print("Source or target node does not exist in nodes of this edge:", edge_ext)
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

  def _handle_multi_modal(self, visual_elements: list[VisualDocumentElement]) -> None:
    with ThreadPoolExecutor() as executor:
      # Submit each visual element to be processed in a separate thread
      executor.map(self._handle_visual, visual_elements)

  def _handle_visual(self, visual_element: VisualDocumentElement) -> None:
    caption = visual_element.caption or "no caption given"

    # Define prompts and model responses based on the visual type
    if visual_element.type == "TABLE":
      prompt_formatted: str = process_template(
        JSON_TABLE,
        {
          "markdown_table": visual_element.content,
          "table_caption": caption,
          "keywords": ", ".join(self.keywords),
        },
      )
      answer = self.model.get_json_response(prompt=prompt_formatted)

    elif visual_element.type == "FIGURE":
      prompt_formatted: str = process_template(
        JSON_FIGURE,
        {"figure_caption": caption, "keywords": ", ".join(self.keywords)},
      )
      answer = self.model.get_multi_modal_response(
        prompt=prompt_formatted, image_path=visual_element.save_location
      )
    else:
      raise ImageProcessingException(f"Unsupported visual type {visual_element.type}")

    # Process the response into entities and relationships
    entities, main_visual_entity_name = self.transform_to_NodeExt(answer)
    json_nodes_edges: NodeEdgeExt = NodeEdgeExt(
      entities=entities, relationships=answer["relationships"]
    )
    if not BuildingTools.check_node_edge_ext(json_nodes_edges):
      print(json_nodes_edges)
      raise NodeCreationException(
        f"{visual_element.type} extraction not in the right format"
      )

    visual_metadata: MetadataVisual = MetadataVisual(
      id=uuid4(),
      content=visual_element.content,
      save_location=visual_element.save_location,
      page_num=visual_element.page_num,
      type=visual_element.type,
    )

    metadata: Metadata = Metadata(
      document_id=visual_element.doc_id, chunk_id=None, visual_metadata=visual_metadata
    )

    self.building_logs.append(
      BuildLog(
        chunk_text=caption
        if visual_element.type == "FIGURE"
        else caption + " --- " + visual_element.content,
        metadata=metadata,
        nodes=json_nodes_edges["entities"],
        edges=json_nodes_edges["relationships"],
        main_visual_entity_name=main_visual_entity_name,
      )
    )

  @staticmethod
  def transform_to_NodeExt(answer: dict[str, Any]) -> tuple[list[NodeExt], str | None]:
    """Transforms the 'entities' key within the `answer` dictionary.

    Ensures that the 'entities' key exists, that its value is a list, and that each entity within that list is a dictionary
    containing the required fields: 'main_node', 'name', and 'description'.

    Args:
      answer (dict): A dictionary representing the response containing the 'entities' key.

    Returns:
      List[NodeExt]: A list of validated entities as dictionaries with 'name' and 'description' fields.

    Raises:
      NodeCreationException: If the 'entities' key is missing, not a list, or contains invalid data.
    """
    main_visual_entity_name: str | None = None
    # Validate that 'entities' exists in answer and is of the correct type
    if "entities" not in answer:
      raise NodeCreationException("'entities' key missing from answer")

    if not isinstance(answer["entities"], list):
      raise NodeCreationException("'entities' in answer is not a list")

    entities: list[NodeExt] = []
    for entity in answer["entities"]:
      # Validate that entity is a dictionary
      if not isinstance(entity, dict):
        raise NodeCreationException(f"Entity {entity} is not a dictionary")

      # Validate that the entity contains 'main_node', 'name', and 'description'
      if all(k in entity for k in ["main_node", "name", "description"]):
        if entity.get("main_node") is True:
          main_visual_entity_name = entity["name"]
        entities.append({"name": entity["name"], "description": entity["description"]})
      else:
        raise NodeCreationException(f"Invalid entity format: {entity}")

    return entities, main_visual_entity_name
