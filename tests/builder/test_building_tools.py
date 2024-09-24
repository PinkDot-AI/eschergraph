from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from faker import Faker

from eschergraph.builder.building_tools import BuildingTools
from eschergraph.builder.models import Chunk
from eschergraph.builder.models import ProcessedFile
from eschergraph.builder.reader.reader import Reader

faker: Faker = Faker()


def test_check_node_ext_pass() -> None:
  valid_node_ext = {"name": "Node1", "description": "A sample node"}
  assert BuildingTools.check_node_ext(valid_node_ext) == True


def test_check_node_ext_fail() -> None:
  invalid_node_ext = {
    "name": "Node1",
    "desc": "A sample node",  # Incorrect key
  }
  assert BuildingTools.check_node_ext(invalid_node_ext) == False


def test_check_edge_ext_pass() -> None:
  valid_edge_ext = {
    "source": "Node1",
    "target": "Node2",
    "relationship": "connected_to",
  }
  assert BuildingTools.check_edge_ext(valid_edge_ext) == True


def test_check_edge_ext_fail() -> None:
  invalid_edge_ext = {
    "source": "Node1",
    "target": "Node2",
    "relation": "connected_to",  # Incorrect key
  }
  assert BuildingTools.check_edge_ext(invalid_edge_ext) == False


def test_check_property_ext_pass() -> None:
  valid_property_ext = {"entity_name": "Entity1", "properties": ["prop1", "prop2"]}
  assert BuildingTools.check_property_ext(valid_property_ext) == True


def test_check_property_ext_fail() -> None:
  invalid_property_ext = {
    "entity_name": "Entity1",
    "properties": "prop1, prop2",  # Incorrect type
  }
  assert BuildingTools.check_property_ext(invalid_property_ext) == False


def test_check_node_edge_ext_pass() -> None:
  valid_node_edge_ext = {
    "entities": [{"name": "Node1", "description": "A sample node"}],
    "relationships": [
      {"source": "Node1", "target": "Node2", "relationship": "connected_to"}
    ],
  }
  assert BuildingTools.check_node_edge_ext(valid_node_edge_ext) == True


def test_check_node_edge_ext_fail() -> None:
  invalid_node_edge_ext = {
    "entities": [
      {"name": "Node1", "desc": "A sample node"}  # Incorrect key
    ],
    "relationships": [
      {"source": "Node1", "target": "Node2", "rel": "connected_to"}  # Incorrect key
    ],
  }
  assert BuildingTools.check_node_edge_ext(invalid_node_edge_ext) == False


def test_process_files_empty() -> None:
  assert BuildingTools.process_files(files=[], multi_modal=False) == []


def test_process_files_single_file() -> None:
  reader_mock: MagicMock = MagicMock(spec=Reader)
  # Set the mock to return itself for initialization
  reader_mock.return_value = reader_mock
  reader_mock.chunks = [
    Chunk(text=text, chunk_id=idx, doc_id=uuid4(), page_num=idx)
    for idx, text in enumerate(faker.texts(nb_texts=15, max_nb_chars=80))
  ]
  reader_mock.total_tokens = 10000
  reader_mock.full_text = faker.text(max_nb_chars=1200)
  reader_mock.visual_elements = None

  processed: list[ProcessedFile] = BuildingTools.process_files(
    files=["./test_files/test.pdf"], multi_modal=False, reader_impl=reader_mock
  )
  processed_file: ProcessedFile = processed[0]

  assert len(processed) == 1
  assert processed_file.chunks == reader_mock.chunks
  assert processed_file.full_text == reader_mock.full_text
  assert processed_file.visual_elements is None
  assert processed_file.document.token_num == reader_mock.total_tokens
  assert processed_file.document.chunk_num == 15
