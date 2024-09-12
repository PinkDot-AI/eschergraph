from __future__ import annotations

from typing import cast

from attrs import asdict
from attrs import fields_dict

from eschergraph.graph.base import EscherBase
from eschergraph.graph.edge import Edge
from eschergraph.graph.loading import LoadState
from eschergraph.graph.node import Node
from eschergraph.graph.property import Property
from eschergraph.persistence.adapters.simple_repository.models import EdgeModel
from eschergraph.persistence.adapters.simple_repository.models import MetadataModel
from eschergraph.persistence.adapters.simple_repository.models import NodeModel
from eschergraph.persistence.adapters.simple_repository.models import PropertyModel


def save_filenames(save_location: str, name: str) -> dict[str, str]:
  """Get the filename for all the pickle files that store the data.

  Args:
    save_location (str): The name of the folder where the data is stored.
    name (str): The name of the graph.

  Returns:
    A dictionary with the attribute name pointing to the filename.
  """
  base_filename: str = save_location + "/" + name
  return {
    "nodes": base_filename + "-nodes.pkl",
    "edges": base_filename + "-edges.pkl",
    "properties": base_filename + "-properties.pkl",
    "doc_node_name_index": base_filename + "-nnindex.pkl",
    "documents": base_filename + "-documents.pkl",
  }


def select_attributes_to_load(object: EscherBase, loadstate: LoadState) -> list[str]:
  """Select the attributes that need to be loaded for an EscherBase object to achieve the desired loadstate.

  Args:
    object (EscherBase): The graph object to determine the attributes for.
    loadstate (LoadState): The desired loadstate of the object.

  Returns:
    A list containing all the attribute names.
  """
  attributes: list[str] = []
  for name, attr in fields_dict(object.__class__).items():
    if "group" not in attr.metadata:
      continue
    if (
      attr.metadata["group"].value > object.loadstate.value
      and attr.metadata["group"].value <= loadstate.value
    ):
      attributes.append(name[1:])
  return attributes


def select_attributes_to_add(object: EscherBase) -> list[str]:
  """Select all the attributes that need to be added to the storage.

  Args:
    object (EscherBase): The object to add to the storage.

  Returns:
    A list containing the attribute names to add.
  """
  attributes: list[str] = []
  for name, attr in fields_dict(object.__class__).items():
    if "group" not in attr.metadata:
      continue
    # The node id is never changed and loadstate not used
    elif attr.metadata["group"] == LoadState.REFERENCE:
      continue
    elif attr.metadata["group"].value <= object.loadstate.value:
      attributes.append(name[1:])
  return attributes


def new_node_to_node_model(node: Node) -> NodeModel:
  """Return a nodemodel for a new node.

  Args:
    node (Node): The node to convert to a NodeModel.

  Returns:
    The NodeModel containing the node's data.
  """
  return {
    "name": node.name,
    "description": node.description,
    "level": node.level,
    "properties": [p.id for p in node.properties],
    "edges": {edge.id for edge in node.edges},
    "community": node.community.node.id if node.community.node else None,
    "metadata": [cast(MetadataModel, asdict(md)) for md in node.metadata],
    "child_nodes": {child.id for child in node.child_nodes},
  }


def new_edge_to_edge_model(edge: Edge) -> EdgeModel:
  """Return an edge model for a new edge.

  Args:
    edge (Edge): The edge to return an EdgeModel for.

  Returns:
    An EdgeModel object containing the edge's data.
  """
  return {
    "frm": edge.frm.id,
    "to": edge.to.id,
    "description": edge.description,
    "metadata": [cast(MetadataModel, asdict(md)) for md in edge.metadata],
  }


def new_property_to_property_model(property: Property) -> PropertyModel:
  """Return a property model for a property.

  Args:
    property (Property): The property to return a PropertyModel for.

  Returns:
    A PropertyModel containing the Property's data.
  """
  return {
    "node": property.node.id,
    "description": property.description,
    "metadata": [cast(MetadataModel, asdict(md)) for md in property.metadata],
  }
