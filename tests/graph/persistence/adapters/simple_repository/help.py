from __future__ import annotations

from typing import cast

from attrs import asdict

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.graph.persistence.adapters.simple_repository.models import (
  MetadataModel,
)
from eschergraph.graph.persistence.adapters.simple_repository.models import NodeModel


def compare_node_to_node_model(node: Node, node_model: NodeModel) -> bool:
  # Check equality for a node being in a community
  if node.community.node and not node_model["community"]:
    return False
  elif not node.community.node and node_model["community"]:
    return False
  elif node.community.node and node_model["community"]:
    if not node.community.node.id == node_model["community"]:
      return False

  if (
    node.report.title != node_model["report"]["title"]
    or node.report.summary != node_model["report"]["summary"]
  ):
    return False
  if node.report.findings is not None:
    if node_model["report"]["findings"] is None:
      return False
    for idx, fnd in enumerate(node.report.findings):
      if (
        fnd.summary != node_model["report"]["findings"][idx]["summary"]
        or fnd.explanation != node_model["report"]["findings"][idx]["explanation"]
      ):
        return False

  return (
    node.name == node_model["name"]
    and node.description == node_model["description"]
    and node.level == node_model["level"]
    and node.properties == node_model["properties"]
    and {edge.id for edge in node.edges} == node_model["edges"]
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
