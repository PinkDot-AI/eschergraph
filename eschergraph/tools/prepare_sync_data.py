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
) -> tuple[
  list[tuple[UUID, str, dict[str, str | int]]],
  list[UUID],
]:
  """Prepares data for synchronization with the vector database.

  Args:
    repository (Repository): The graph's repository.

  Returns:
    tuple: A tuple containing lists of documents, IDs, metadata, and IDs to delete.
  """
  change_logs: list[ChangeLog] = repository.get_change_log()

  # Map each object id to its change_logs
  objects_logs: dict[UUID, list[ChangeLog]] = {log.id: [] for log in change_logs}
  for log in change_logs:
    objects_logs[log.id].append(log)

  ids_to_create, ids_to_delete = _get_actions_for_objects(objects_logs)
  create_main: list[tuple[UUID, str, dict[str, str | int]]] = []

  for id in ids_to_create:
    cur_log: ChangeLog = objects_logs[id][0]
    # Prepare metadata based on log type
    if cur_log.type == Node:
      node: Node | None = repository.get_node_by_id(id)
      if not node:
        continue
      # add node description
      md_node: dict[str, str | int] = {
        "level": log.level,
        "type": "node",
        "entity_frm": node.name,
        "entity_to": "",
      }
      node_string = node.name + ", " + node.description
      create_main.append((id, node_string, md_node))

    elif cur_log.type == Edge:
      edge: Edge | None = repository.get_edge_by_id(id)
      if not edge:
        continue
      md_edge: dict[str, str | int] = {
        "level": log.level,
        "type": "edge",
        "entity_frm": edge.frm.name,
        "entity_to": edge.to.name,
      }
      create_main.append((id, edge.description, md_edge))

    elif cur_log.type == Property:
      property: Property | None = repository.get_property_by_id(id)
      if not property:
        continue
      md_prop: dict[str, str | int] = {
        "level": log.level,
        "type": "property",
        "entity_frm": property.node.name,
        "entity_to": "",
      }
      property_string = property.node.name + ", " + property.description
      create_main.append((id, property_string, md_prop))

  return create_main, ids_to_delete


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
