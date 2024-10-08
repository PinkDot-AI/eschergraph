from __future__ import annotations

from typing import cast

from attrs import asdict

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph import Property
from eschergraph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.persistence.adapters.simple_repository.models import (
  MetadataModel,
)
from eschergraph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.persistence.adapters.simple_repository.models import (
  PropertyModel,
)


def compare_node_to_node_model(node: Node, node_model: NodeModel) -> bool:
  # Check equality for a node being in a community
  if node.community.node and not node_model["community"]:
    return False
  elif not node.community.node and node_model["community"]:
    return False
  elif node.community.node and node_model["community"]:
    if not node.community.node.id == node_model["community"]:
      return False

  return (
    node.name == node_model["name"]
    and node.description == node_model["description"]
    and node.level == node_model["level"]
    and {edge.id for edge in node.edges} == node_model["edges"]
    and [property.id for property in node.properties] == node_model["properties"]
    and [cast(MetadataModel, asdict(md)) for md in node.metadata]
    == node_model["metadata"]
  )


def compare_edge_to_edge_model(edge: Edge, edge_model: EdgeModel) -> bool:
  return (
    edge.frm.id == edge_model["frm"]
    and edge.to.id == edge_model["to"]
    and edge.description == edge_model["description"]
    and [cast(MetadataModel, asdict(md)) for md in edge.metadata]
    == edge_model["metadata"]
  )


def compare_property_to_property_model(
  property: Property, property_model: PropertyModel
) -> bool:
  return (
    property.node.id == property_model["node"]
    and property.description == property_model["description"]
  )
