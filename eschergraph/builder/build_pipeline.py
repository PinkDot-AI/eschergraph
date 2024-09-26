from __future__ import annotations

import time
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
from eschergraph.builder.models import Chunk
from eschergraph.builder.models import ProcessedFile
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.config import JSON_BUILD
from eschergraph.config import JSON_FIGURE
from eschergraph.config import JSON_KEYWORDS
from eschergraph.config import JSON_PROPERTY
from eschergraph.config import JSON_TABLE
from eschergraph.config import SUMMARY
from eschergraph.exceptions import ExternalProviderException
from eschergraph.exceptions import ImageProcessingException
from eschergraph.exceptions import NodeCreationException
from eschergraph.graph.community import Community
from eschergraph.graph.node import Node
from eschergraph.graph.property import Property
from eschergraph.persistence.document import Document
from eschergraph.persistence.metadata import Metadata
from eschergraph.persistence.metadata import MetadataVisual
from eschergraph.tools.community_builder import build_community_layer
from eschergraph.tools.node_matcher import NodeMatcher

if TYPE_CHECKING:
  from eschergraph.graph.graph import Graph


@define
class BuildPipeline:
  """The build pipeline that converts chunks into objects to add to the graph."""

  model: ModelProvider
  reranker: Reranker
  building_logs: list[BuildLog] = field(factory=list)
  unique_entities: list[str] = field(factory=list)
  keywords: list[str] = field(factory=list)

  def run(self, graph: Graph, processed_file: ProcessedFile) -> list[BuildLog]:
    """Run the build pipeline with time tracking.

    Returns:
      A list of build logs that can be used to add nodes and edges to the graph.
    """
    total_start_time = time.time()  # Track the total time

    # Step 1: extract the document keywords and summary
    step_1_start_time = time.time()
    self._extract_keywords(full_text=processed_file.full_text)
    summary: str = self._get_summary(self.model, full_text=processed_file.full_text)
    step_1_end_time = time.time()
    print(
      f"Step 1: Extracting keywords and summary took {step_1_end_time - step_1_start_time:.4f} seconds"
    )

    # Step 2: extract nodes and edges
    step_2_start_time = time.time()
    self._extract_node_edges(processed_file.chunks)
    step_2_end_time = time.time()
    print(
      f"Step 2: Extracting nodes and edges took {step_2_end_time - step_2_start_time:.4f} seconds"
    )

    # Step 3: extract properties
    step_3_start_time = time.time()
    self._extract_properties()
    step_3_end_time = time.time()
    print(
      f"Step 3: Extracting properties took {step_3_end_time - step_3_start_time:.4f} seconds"
    )

    # Step 4: Handle multi-modal content if present
    if processed_file.visual_elements:
      step_4a_start_time = time.time()
      self._handle_multi_modal(processed_file.visual_elements)
      step_4a_end_time = time.time()
      print(
        f"Step 4a: Handling multi-modal elements took {step_4a_end_time - step_4a_start_time:.4f} seconds"
      )

    # Step 5: Use the node matcher to match duplicate nodes
    step_4_start_time = time.time()
    unique_entities: list[str] = self._get_unique_entities()
    updated_logs: list[BuildLog] = NodeMatcher(
      model=self.model, reranker=self.reranker
    ).match(
      building_logs=self.building_logs,
      unique_node_names=unique_entities,
    )
    step_4_end_time = time.time()
    print(
      f"Step 4: Node matching took {step_4_end_time - step_4_start_time:.4f} seconds"
    )

    # Step 6: Convert building logs into nodes and edges
    step_5_start_time = time.time()
    num_nodes: int = self._persist_to_graph(graph=graph, updated_logs=updated_logs)
    step_5_end_time = time.time()
    print(
      f"Step 5: Persisting to graph took {step_5_end_time - step_5_start_time:.4f} seconds"
    )

    # Step 7: Build the community layer
    step_6_start_time = time.time()
    comm_nodes: list[Node] = build_community_layer(graph, processed_file, num_nodes)
    step_6_end_time = time.time()
    print(
      f"Step 6: Building community layer took {step_6_end_time - step_6_start_time:.4f} seconds"
    )

    # Step 8: Add the document node
    step_7_start_time = time.time()
    self._create_document_node(
      graph, comm_nodes, summary, processed_file.document, self.keywords
    )
    step_7_end_time = time.time()
    print(
      f"Step 7: Adding document node took {step_7_end_time - step_7_start_time:.4f} seconds"
    )

    # Step 9: Sync the graph and save to repository
    step_8_start_time = time.time()
    graph.sync_vectordb()
    graph.repository.save()
    step_8_end_time = time.time()
    print(
      f"Step 8: Syncing graph and saving took {step_8_end_time - step_8_start_time:.4f} seconds"
    )

    total_end_time = time.time()
    print(f"Total time taken: {total_end_time - total_start_time:.4f} seconds")

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
      raise ExternalProviderException("keywords extraction not in correct format")

  @staticmethod
  def _get_summary(model: ModelProvider, full_text: str) -> str:
    prompt_formatted: str = process_template(SUMMARY, {"full_text": full_text})
    summary: str | None = model.get_plain_response(prompt=prompt_formatted)

    if not summary:
      raise ExternalProviderException("An empty summary was returned")

    return summary

  @staticmethod
  def _create_document_node(
    graph: Graph,
    comm_nodes: list[Node],
    summary: str,
    document: Document,
    keywords: list[str],
  ) -> Node:
    """Create the document node.

    Args:
      graph (Graph): The graph to add the document node to.
      comm_nodes (list[Node]): The community nodes for this document.
      summary (str): The summary for the document.
      document (Document): The document data object.
      keywords (list[str]): A list of keywords.
    """
    doc_node: Node = Node.create(
      name=document.name,
      repository=graph.repository,
      description=summary,
      level=2,
    )
    doc_node.id = document.id
    # Add all the keywords as properties
    for keyword in keywords:
      Property.create(node=doc_node, description=keyword)

    # Set the community nodes as child nodes
    doc_node.child_nodes = comm_nodes

    graph.repository.add(doc_node)

    # Set the doc node as parent node
    for comm in comm_nodes:
      comm.community = Community(node=doc_node)
      graph.repository.add(comm)

    return doc_node

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

  def _persist_to_graph(self, graph: Graph, updated_logs: list[BuildLog]) -> int:
    """Add nodes, edges, and properties to the graph at level 0.

    Returns:
      int: The number of nodes at level 0.
    """
    num_nodes: int = 0
    # first add all nodes
    for log in updated_logs:
      # add conditional is_visual to the node if the buildinglogs says so
      for node_ext in log.nodes:
        is_visual: bool = False
        if (
          log.main_visual_entity_name
          and log.main_visual_entity_name.lower() == node_ext["name"].lower()
        ):
          is_visual = True

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
        num_nodes += 1

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

    return num_nodes

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
      prompt_formatted = process_template(
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
    if not BuildingTools.check_node_edge_ext(cast(dict[str, Any], json_nodes_edges)):
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
