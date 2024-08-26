from __future__ import annotations

from typing import Any
from uuid import UUID

from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence.change_log import Action
from eschergraph.graph.persistence.repository import Repository
from eschergraph.graph.property import Property


def prepare_sync_data(
  repository: Repository, level: int = 0
) -> tuple[list[str], list[UUID], list[dict[str, Any]], list[UUID]]:
  """Prepares data for synchronization with the vector database.

  Args:
      level (int, optional): The hierarchical level at which the metadata is being synced. Default is 0.
      repository (Repository): The regarding graphs repository
  Returns:
      tuple: A tuple containing lists of documents, IDs, metadata, and IDs to delete.
  """
  docs: list[str] = []
  ids: list[UUID] = []
  metadata: list[dict[str, object]] = []
  ids_to_delete: list[UUID] = []

  for log in repository.get_change_log():
    # Handle deletion and update actions
    if log.action in {Action.UPDATE, Action.DELETE}:
      ids_to_delete.append(log.id)
      if log.action == Action.DELETE:
        continue

    # Prepare metadata based on log type
    metadata_entry = {"level": level, "chunk_id": "", "document_id": ""}
    if log.type == Node:
      node: Node | None = repository.get_node_by_id(log.id)
      if not node:
        continue
      docs.append(node.name)
      metadata_entry.update({
        "type": "node",
        "entity_frm": "",
        "entity_to": "",
      })
    elif log.type == Edge:
      edge: Edge | None = repository.get_edge_by_id(log.id)
      if not edge:
        continue
      docs.append(edge.description)
      metadata_entry.update({
        "type": "edge",
        "entity_frm": edge.frm.name,
        "entity_to": edge.to.name,
      })
    elif log.type == Property:
      property: Property | None = repository.get_property_by_id(log.id)
      if not property:
        continue
      docs.append(property.description)
      metadata_entry.update({
        "type": "property",
        "entity_frm": property.node.name,
        "entity_to": "",
      })
    else:
      continue  # Skip logs that are neither Node, Edge, nor Property
    metadata.append(metadata_entry)
    ids.append(log.id)

  return docs, ids, metadata, ids_to_delete
