from __future__ import annotations

from uuid import UUID

from eschergraph.graph.edge import Edge
from eschergraph.graph.node import Node
from eschergraph.graph.property import Property
from eschergraph.persistence.change_log import Action
from eschergraph.persistence.change_log import ChangeLog
from eschergraph.persistence.repository import Repository


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

      # We add the document_id to all the object
      md_node: dict[str, str | int] = {
        "level": cur_log.level,
        "type": "node",
        "document_id": _get_node_document_id(node),
      }
      node_string = node.name + ", " + node.description
      create_main.append((id, node_string, md_node))

    elif cur_log.type == Edge:
      edge: Edge | None = repository.get_edge_by_id(id)
      if not edge:
        continue
      md_edge: dict[str, str | int] = {
        "level": cur_log.level,
        "type": "edge",
        "document_id": _get_node_document_id(edge.frm),
      }
      create_main.append((id, edge.description, md_edge))

    elif cur_log.type == Property:
      property: Property | None = repository.get_property_by_id(id)
      if not property:
        continue
      md_prop: dict[str, str | int] = {
        "level": cur_log.level,
        "type": "property",
        "document_id": _get_node_document_id(property.node),
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


def _get_node_document_id(node: Node) -> str:
  """Returns the UUID of the node's document_id in string format.

  Currently, all graph objects do still exclusively belong to a single
  document as we have not added inter-document merging or
  edge finding. As soon as this is added, this logic will change.

  Args:
    node (Node): The node to get the document_id for.

  Returns:
    The UUID as a string.
  """
  cur_level: int = node.level
  cur_node: Node = node

  # Get the metadata on a level 0 child node
  while cur_level > 0:
    cur_node = cur_node.child_nodes[0]
    cur_level -= 1

  return str(next(iter(cur_node.metadata)).document_id)
