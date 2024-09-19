from __future__ import annotations

from eschergraph.builder.building_tools import BuildingTools


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
