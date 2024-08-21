from __future__ import annotations

import datetime
import json
import os
import pickle
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from typing import Optional

from attrs import define
from attrs import Factory

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.exceptions import ExternalProviderException
from eschergraph.exceptions import FileTypeNotProcessableException
from eschergraph.graph.graph import Graph
from eschergraph.graph.node import Node
from eschergraph.graph.node import Property
from eschergraph.graph.persistence.metadata import Metadata
from eschergraph.tools.reader import Chunk
from eschergraph.tools.reader import Reader

JSON_BUILD = "json_build.jinja"
JSON_PROPERTY = "json_property.jinja"


@define
class BuildLogItem:
  """This is the dataclass for the building logs."""

  chunk: str
  node_edge_json: dict[str, list[dict[str, str]]]
  properties_json: Any | None
  metadata: Metadata


@define
class Build:
  """This is the main class for the graph building pipeline."""

  file_location: str
  model: OpenAIProvider
  use_edge_weights: Optional[bool] = True
  _reader: Optional[Reader] = None
  _graph: Optional[Graph] = None
  save_location: Optional[str] = "./eschergraph-storage"
  filename: Optional[str] = None
  building_logs: list[BuildLogItem] = Factory(list)

  def __init__(
    self,
    file_location: str,
    save_location: Optional[str] = None,
    use_edge_weights: Optional[bool] = None,
    model: Optional[str] = None,
  ) -> None:
    """Initializes the Build object with the provided configurations.

    It sets up the save location, model, reader, and graph. If any parameters are not provided,
    defaults are used. Raises an exception if no filename is provided.

    Args:
        file_location ([str): The name of the file location(path) to be processed.
        save_location (Optional[str]): The location to save the final graph and logs.
        use_edge_weights (Optional[bool]): Whether to use edge weights in the graph.
        model (Optional[str]): The model to be used for processing.
    """
    if not save_location:
      save_location = "./eschergraph-storage"
    if not use_edge_weights:
      use_edge_weights = True
    if not model:
      model = "gpt-4o-mini"
    if not file_location:
      raise FileTypeNotProcessableException("Cannot build graph without a file")

    self.save_location = save_location
    self.use_edge_weights = use_edge_weights
    self.model = OpenAIProvider(
      OpenAIModel.GPT_4o_MINI,
      api_key=os.environ["OPENAI_API_KEY"],
    )
    self.filename = os.path.splitext(os.path.basename(file_location))[0]
    self.building_logs: list[BuildLogItem] = []

  @property
  def graph(self) -> Graph:
    """Lazy initialization of the graph."""
    if self._graph is None:
      self._graph = Graph(name="name")
    return self._graph

  @property
  def reader(self) -> Reader:
    """Lazy initialization of the reader."""
    if self._reader is None:
      self._reader = Reader(
        file_location=self.file_location,
      )
    return self._reader

  def run(self) -> Graph:
    """Executes the entire graph-building process.

    This includes parsing the file, estimating cost and time, building the graph,
    handling node and edge properties, merging nodes, creating a vector database, saving the graph, and saving logs.

    Returns:
        Graph: The constructed graph after processing.
    """
    self.reader.parse()
    # Cost & time estimation
    print(
      f"Processing {len(self.reader.chunks)} chunks using {self.reader.total_tokens} tokens."
      f"\nEstimated cost: ${self._get_cost_indication()} using {self.model.model.value}"
      f"\nExpected completion time: {self._get_time_indication()}."
    )

    # Build graph
    self._build_graph()

    # Add properties

    # Remove unmatched nodes

    # Merge nodes and remove duplicates

    # Create vector database

    # Save graph
    self._save_graph()

    # Save logs in location
    self._save_logs_to_json_file()

    # Visualize
    return self.graph

  def _handle_chunk_building(self, chunk: Chunk) -> None:
    """Handles the process of building a graph from a single chunk of text.

    It sends a prompt to the model, receives the JSON response, and adds
    nodes and edges to the graph based on that response.

    Args:
        chunk (Chunk): A chunk of text to be processed.
    """
    prompt_send: str = process_template(JSON_BUILD, {"input_text": chunk.text})
    json_nodes_edge: dict[str, list[dict[str, str]]] = self._get_json_response(
      prompt=prompt_send
    )
    metadata: Metadata = Metadata(document_id=chunk.doc_id, chunk_id=chunk.chunk_id)
    for entity in json_nodes_edge["entities"]:
      # Add the nodes (if they do not yet exist)
      if self.graph.repository.get_node_by_name(
        entity["name"].lower(), document_id=chunk.doc_id
      ):
        continue

      self.graph.add_node(
        name=entity["name"],
        description=entity["description"],
        level=0,
        metadata=metadata,
      )

    for edge in json_nodes_edge["relationships"]:
      to_node: Node | None = self.graph.repository.get_node_by_name(
        edge["source"].lower(), document_id=chunk.doc_id
      )
      from_node: Node | None = self.graph.repository.get_node_by_name(
        edge["target"].lower(), document_id=chunk.doc_id
      )
      if to_node and from_node:
        self.graph.add_edge(
          frm=from_node,
          to=to_node,
          description=edge["relationship"],
          metadata=metadata,
        )

    # Add to building logger
    self.building_logs.append(
      BuildLogItem(
        chunk=chunk.text,
        node_edge_json=json_nodes_edge,
        properties_json=None,
        metadata=metadata,
      )
    )

  def _add_properties(self) -> None:
    """This is the main properties function that threads the llm calles to add propeties."""
    with ThreadPoolExecutor(max_workers=10) as executor:
      futures = {
        executor.submit(self._handle_property_chunk, item): item
        for item in self.building_logs
      }
      for future in as_completed(futures):
        try:
          future.result()
        except Exception as e:
          print(f"Error processing property: {e}")

  def _handle_property_chunk(self, logitem: BuildLogItem) -> None:
    """'This is the function for adding properties to the nodes."""
    node_names: list[str] = [e["name"] for e in logitem.node_edge_json["entities"]]

    if len(node_names) == 0:
      print("No extracted nodes found in this chunk")
      return

    property_prompt: str = process_template(
      JSON_PROPERTY,
      {"current_nodes": ", ".join(node_names), "input_text": logitem.chunk},
    )

    entity_prop_dict: dict[str, list[dict[str, list[str]]]] = self._get_json_response(
      property_prompt
    )
    for entity in entity_prop_dict["entities"]:
      for node_name_key, properties in entity.items():
        node_name: str = node_name_key.lower()
        node: Node | None = self.graph.repository.get_node_by_name(
          node_name, document_id=logitem.metadata.document_id
        )
        if not node:
          print("This node does not yet exist")
          print(node_name)
          return
        for property in properties:
          node.properties.append(
            Property(description=property, metadata=logitem.metadata)
          )
    logitem.properties_json = entity_prop_dict

  def _build_graph(self) -> None:
    """Builds the graph by processing each chunk of the document in parallel using a ThreadPoolExecutor.

    Each chunk is handled by the _handle_chunk_building
    method. Logs any errors encountered during the process.
    """
    with ThreadPoolExecutor(max_workers=10) as executor:
      futures = {
        executor.submit(self._handle_chunk_building, chunk): chunk
        for chunk in self.reader.chunks
      }
      for future in as_completed(futures):
        try:
          future.result()  # We can handle results or exceptions here if needed
        except Exception as e:
          print(f"Error processing chunk: {e}")

  def _save_logs_to_json_file(
    self, save_location: str = "/eschergraph-storage"
  ) -> None:
    """Saves the building logs to a JSON file. The logs are sorted by chunk_id and saved in a serializable format.

    Creates the save directory if it does not exist.

    Args:
        save_location (str): The directory location where the JSON file should be saved.
    """
    # Create the directory if it does not exist
    Path(save_location).mkdir(parents=True, exist_ok=True)

    # Sort the building logs by chunk_id in increasing order
    sorted_logs: list[BuildLogItem] = sorted(
      self.building_logs, key=lambda log_item: log_item.metadata.chunk_id
    )

    # Convert the sorted logs to a serializable format
    logs_serializable: list[dict[str, str | dict[str, str]]] = []
    for log_item in sorted_logs:
      log_dict: dict[str, Any] = {
        "chunk": log_item.chunk,
        "node_edge_json": log_item.node_edge_json,
        "properties_json": log_item.properties_json,
        "metadata": {
          "document_id": str(log_item.metadata.document_id),
          "chunk_id": log_item.metadata.chunk_id,
        },
      }
      logs_serializable.append(log_dict)

    # Define the full path for the JSON file
    file_path: Path = Path(save_location) / f"building-logs-{self.filename}-graph.json"

    # Save the logs to the JSON file
    with open(file_path, "w", encoding="utf-8") as json_file:
      json.dump(logs_serializable, json_file, indent=4)

  def _get_json_response(self, prompt: str) -> Any:
    """Sends a prompt to the model to get a JSON response and parses it into a Python dictionary.

    Args:
        prompt (str): The prompt to be sent to the model.

    Returns:
        dict: The JSON response parsed as a Python dictionary.
    """
    response: str | None = self.model.get_json_response(prompt, temperature=0.1)
    if response is None:
      raise ValueError("The model returned None, expected a JSON string.")

    try:
      return json.loads(response)
    except json.JSONDecodeError as e:
      raise ValueError(f"Failed to decode JSON response: {e}")

  def _get_cost_indication(self) -> float:
    """Estimates the cost based on the number of tokens andthe model used.

    The completion tokens are assumed to be equal to prompt tokens.

    Returns:
        float: The estimated cost of processing.
    """
    model = self.model.model.value
    total_tokens = self.reader.total_tokens

    # Initialize variables
    prompt_cost: float = 0.0
    completion_cost: float = 0.0

    # Assumed that completion tokens are equal to prompt tokens
    if model == "gpt-4o":
      prompt_cost = (total_tokens / 1e6) * 5.00
      completion_cost = (total_tokens / 1e6) * 15.00
    elif model == "gpt-4o-mini":
      prompt_cost = (total_tokens / 1e6) * 0.150
      completion_cost = (total_tokens / 1e6) * 0.600
    else:
      raise ExternalProviderException("Invalid model specified.")

    total_cost: float = prompt_cost + completion_cost / 3
    return round(total_cost, 3)

  def _get_time_indication(self) -> str:
    """Estimates the time required to process the document based on the number of chunks, the model used, and the number of parallel workers.

    Returns:
        float: The estimated time to complete the processing.
    """
    average_time_per_chunk: int = 0
    if self.model.model.value == "gpt-4o":
      average_time_per_chunk = 4  # seconds
    else:
      average_time_per_chunk = 2  # seconds

    num_chunks: int = len(self.reader.chunks)
    max_workers: int = 10  # as used in ThreadPoolExecutor

    # If number of chunks is less than or equal to max_workers,
    # the time taken would be approximately the time for one chunk.
    if num_chunks <= max_workers:
      estimated_time = average_time_per_chunk
    else:
      # Calculate the time for full batches and any remaining chunks
      full_batches = num_chunks // max_workers
      remaining_chunks = num_chunks % max_workers

      estimated_time = full_batches * average_time_per_chunk
      if remaining_chunks > 0:
        estimated_time += average_time_per_chunk

    # If the estimated time is more than 60 seconds, return time in minutes
    if estimated_time > 60:
      minutes = round(estimated_time // 60, 3)
      return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
      return f"{round(estimated_time, 3)} seconds"

  def _save_graph(self) -> None:
    """Saves the constructed graph to a file in the specified location.

    The filename is generated based on the save location, model, use of edge weights, and timestamp.
    """
    if self.save_location:
      location: str = self.save_location + str(self.model.model.value)

    if self.use_edge_weights:
      location += "-with_weights-"
    else:
      location += "-no_weights-"
    if self.filename:
      location += f"{self.filename}-"

    location += datetime.datetime.now().strftime("%Y%m%d%H%M") + ".pkl"
    with open(location, "wb") as file:
      pickle.dump(self.graph, file)
