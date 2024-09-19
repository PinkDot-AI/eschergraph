from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

import pytest

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.builder.reader.multi_modal.data_structure import VisualDocumentElement
from eschergraph.graph.node import Node
from eschergraph.persistence import Metadata
from eschergraph.persistence.adapters.simple_repository import SimpleRepository

if TYPE_CHECKING:
  from eschergraph.graph import Graph


@pytest.fixture(scope="function")
def builder_mock() -> BuildPipeline:
  openai_mock = MagicMock(spec=OpenAIProvider)
  jina_mock = MagicMock(spec=JinaReranker)
  return BuildPipeline(model=openai_mock, reranker=jina_mock)


# Mock VisualDocumentElements
mock_figure_1 = VisualDocumentElement(
  content="A bar chart showing sales data",
  caption="Figure 1: Monthly Sales Data",
  save_location="/path/to/figure1.png",
  page_num=1,
  doc_id=UUID("12345678-1234-5678-1234-567812345678"),
  type="figure",
)

mock_figure_2 = VisualDocumentElement(
  content="A line graph of temperature changes",
  caption="Figure 2: Annual Temperature Trends",
  save_location="/path/to/figure2.png",
  page_num=2,
  doc_id=UUID("87654321-4321-8765-4321-876543210987"),
  type="figure",
)

mock_figure_3 = VisualDocumentElement(
  content="A pie chart of market share",
  caption=None,
  save_location="/path/to/figure3.png",
  page_num=3,
  doc_id=UUID("11111111-2222-3333-4444-555555555555"),
  type="figure",
)
# Mock VisualDocumentElement for a table
mock_table = VisualDocumentElement(
  content="| Column1 | Column2 |\n|---------|---------||\n| Data1   | Data2   |",
  caption="Table 1: Sample Data",
  save_location="/path/to/table1.png",
  page_num=4,
  doc_id=UUID("22222222-3333-4444-5555-666666666666"),
  type="table",
)


def test_build_figure(
  tmp_path: Path, builder_mock: BuildPipeline, graph_unit: Graph
) -> None:
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  graph_unit.name = "test graph"
  graph_unit.repository = repository
  # Mock the model's response
  mock_response = {
    "entities": [
      {
        "name": "Market Share",
        "description": "Distribution of market share among competitors",
      },
      {
        "name": "Competitors",
        "description": "Various companies competing in the market",
      },
    ],
    "relationships": [
      {"source": "Market Share", "target": "Competitors", "relationship": "belongs to"}
    ],
  }
  builder_mock.model.get_multi_modal_response = lambda **kwargs: mock_response

  # Call the method under test
  builder_mock._handle_figure(mock_figure_3)

  # Assertions
  assert len(builder_mock.building_logs) == 1, "Expected one BuildLog to be added"

  build_log = builder_mock.building_logs[0]
  assert (
    build_log.chunk_text == "no caption given"
  ), "Expected 'no caption given' for a figure without caption"

  assert build_log.metadata.document_id == mock_figure_3.doc_id, "Document ID mismatch"
  assert build_log.metadata.chunk_id is None, "Expected chunk_id to be None for figures"

  visual_metadata = build_log.metadata.visual_metadata
  assert visual_metadata is not None, "Expected visual_metadata to be present"
  assert visual_metadata.content == mock_figure_3.content, "Content mismatch"
  assert (
    visual_metadata.save_location == mock_figure_3.save_location
  ), "Save location mismatch"
  assert visual_metadata.page_num == mock_figure_3.page_num, "Page number mismatch"
  assert visual_metadata.type == mock_figure_3.type, "Type mismatch"

  assert len(build_log.nodes) == 2, "Expected two nodes to be extracted"
  assert len(build_log.edges) == 1, "Expected one edge to be extracted"

  # Verify the content of nodes and edges
  assert any(
    node["name"] == "Market Share" for node in build_log.nodes
  ), "Expected 'Market Share' node"
  assert any(
    node["name"] == "Competitors" for node in build_log.nodes
  ), "Expected 'Competitors' node"
  assert (
    build_log.edges[0]["source"] == "Market Share"
  ), "Expected edge source to be 'Market Share'"
  assert (
    build_log.edges[0]["target"] == "Competitors"
  ), "Expected edge target to be 'Competitors'"


def test_handle_table(
  tmp_path: Path, builder_mock: BuildPipeline, graph_unit: Graph
) -> None:
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  graph_unit.name = "test graph"
  graph_unit.repository = repository

  # Mock the model's response
  mock_response = {
    "entities": [
      {"name": "Column1", "description": "First column of the table"},
      {"name": "Column2", "description": "Second column of the table"},
      {"name": "Data1", "description": "Data in the first column"},
      {"name": "Data2", "description": "Data in the second column"},
    ],
    "relationships": [
      {"source": "Column1", "target": "Data1", "relationship": "contains"},
      {"source": "Column2", "target": "Data2", "relationship": "contains"},
    ],
  }
  builder_mock.model.get_json_response = lambda **kwargs: mock_response

  # Set keywords for the builder
  builder_mock.keywords = ["sample", "data"]

  # Call the method under test
  builder_mock._handle_table(mock_table)

  # Assertions
  assert len(builder_mock.building_logs) == 1, "Expected one BuildLog to be added"

  build_log = builder_mock.building_logs[0]
  expected_chunk_text = f"Table 1: Sample Data --- {mock_table.content}"
  assert build_log.chunk_text == expected_chunk_text, "Chunk text mismatch"

  assert build_log.metadata.document_id == mock_table.doc_id, "Document ID mismatch"
  assert build_log.metadata.chunk_id is None, "Expected chunk_id to be None for tables"

  visual_metadata = build_log.metadata.visual_metadata
  assert visual_metadata is not None, "Expected visual_metadata to be present"
  assert visual_metadata.content == mock_table.content, "Content mismatch"
  assert (
    visual_metadata.save_location == mock_table.save_location
  ), "Save location mismatch"
  assert visual_metadata.page_num == mock_table.page_num, "Page number mismatch"
  assert visual_metadata.type == mock_table.type, "Type mismatch"

  assert len(build_log.nodes) == 4, "Expected four nodes to be extracted"
  assert len(build_log.edges) == 2, "Expected two edges to be extracted"

  # Verify the content of nodes and edges
  node_names = [node["name"] for node in build_log.nodes]
  assert set(node_names) == {
    "Column1",
    "Column2",
    "Data1",
    "Data2",
  }, "Unexpected node names"

  edge_relations = [
    (edge["source"], edge["target"], edge["relationship"]) for edge in build_log.edges
  ]
  assert (
    "Column1",
    "Data1",
    "contains",
  ) in edge_relations, "Expected edge relation missing"
  assert (
    "Column2",
    "Data2",
    "contains",
  ) in edge_relations, "Expected edge relation missing"


# TODO: refactor to use a mock for the repository
def test_persist_to_graph(
  tmp_path: Path, builder_mock: BuildPipeline, graph_unit: Graph
) -> None:
  repository: SimpleRepository = SimpleRepository(save_location=tmp_path.as_posix())

  graph_unit.name = "test graph"
  graph_unit.repository = repository

  # Prepare build logs
  build_logs = [
    BuildLog(
      metadata=Metadata(document_id=uuid4(), chunk_id=4),
      nodes=[
        NodeExt(name="node 1", description="node 1 is cool"),
        NodeExt(name="node 2", description="node 2 is medium"),
      ],
      edges=[
        EdgeExt(source="node 1", target="node 2", relationship="node 1 loves node 2")
      ],
      properties=[
        PropertyExt(
          entity_name="node 1",
          properties=["node 1 is very cool", "node 1 has many friends"],
        )
      ],
      chunk_text="node 1 is in love with node 2. Node 1 is cool, very cool and has many friends. Node 2 is medium",
    ),
    BuildLog(
      metadata=Metadata(document_id=uuid4(), chunk_id=4),
      nodes=[NodeExt(name="node 2", description="node 2 does not like langchain")],
      edges=[],
      properties=[],
      chunk_text="mock",
    ),
  ]

  # Call the method under test
  builder_mock._persist_to_graph(graph_unit, build_logs)

  # Fetch all nodes from the repository
  all_nodes: list[Node] = repository.get_all_at_level(0)
  node_names = [n.name for n in all_nodes]

  # Assert that the correct nodes were added
  assert set(node_names) == {
    "node 1",
    "node 2",
  }, f"Expected nodes {'node 1', 'node 2'}, but got {set(node_names)}"

  # Verify that the properties and edges were correctly added for each node
  for node in all_nodes:
    if node.name == "node 1":
      # Check properties of node 1
      expected_properties = ["node 1 is very cool", "node 1 has many friends"]
      actual_properties = [prop.description for prop in node.properties]
      assert set(actual_properties) == set(
        expected_properties
      ), f"Expected properties {expected_properties}, but got {actual_properties}"

    if node.name == "node 2":
      properties = node.properties
      # Node 2 does not have properties or edges in the second log entry
      assert (
        len(properties) == 0
      ), f"Expected no properties for 'node 2', but got {len(properties)}"

  # TODO: no method to test the edges yet.
