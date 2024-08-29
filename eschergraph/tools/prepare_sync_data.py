from __future__ import annotations

from uuid import UUID

from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.persistence.change_log import Action
from eschergraph.graph.persistence.change_log import ChangeLog
from eschergraph.graph.persistence.repository import Repository
from eschergraph.graph.property import Property


def prepare_sync_data(
  repository: Repository,
) -> tuple[list[str], list[UUID], list[dict[str, str]], list[UUID]]:
  """Prepares data for synchronization with the vector database.

  Args:
    repository (Repository): The graph's repository.

  Returns:
    tuple: A tuple containing lists of documents, IDs, metadata, and IDs to delete.
  """
  docs: list[str] = []
  metadata: list[dict[str, str | int]] = []
  change_logs: list[ChangeLog] = repository.get_change_log()

  # Map each object id to its change_logs
  objects_logs: dict[UUID, list[ChangeLog]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    objects_logs[log.id].append(log)

  ids_to_create, ids_to_delete = _get_actions_for_objects(objects_logs)

  # Remove change logs that contain a create and delete for the same object
  for id in ids_to_create:
    log: ChangeLog = objects_logs[id][0]
    # Prepare metadata based on log type
    metadata_entry = {"level": log.level, "chunk_id": "", "document_id": ""}
    if log.type == Node:
      node: Node | None = repository.get_node_by_id(id)
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

    metadata.append(metadata_entry)

  return docs, ids_to_create, metadata, ids_to_delete


def _get_actions_for_objects(
  objects_logs: dict[UUID, list[ChangeLog]],
) -> tuple[list[UUID], list[UUID]]:
  ids_to_delete: list[UUID] = []
  ids_to_create: list[UUID] = []
  for id, object_logs in objects_logs.items():
    # Create a set of actions for the object
    actions: set[Action] = {log.action for log in object_logs}
    if not Action.CREATE in actions:
      ids_to_delete.append(id)
    if not Action.DELETE in actions:
      ids_to_create.append(id)

  return ids_to_create, ids_to_delete
