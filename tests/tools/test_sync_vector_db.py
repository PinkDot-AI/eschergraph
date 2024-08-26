# from __future__ import annotations
# from uuid import uuid4
# from eschergraph.graph.edge import Edge
# from eschergraph.graph.node import Node
# from eschergraph.graph.persistence.change_log import Action
# from eschergraph.graph.persistence.change_log import ChangeLog
# from eschergraph.graph.property import Property
# from eschergraph.tools.prepare_sync_data import prepare_sync_data
# def test_prep_sync_vector_db() -> None:
#   """This is a test function for the prep sync vector db."""
#   level: int = 0
#   change_logs: list[ChangeLog] = [
#     ChangeLog(id=uuid4(), action=Action.DELETE, type=Node, attributes=["apple"]),
#     ChangeLog(id=uuid4(), action=Action.CREATE, type=Node, attributes=["apple"]),
#     ChangeLog(
#       id=uuid4(),
#       action=Action.CREATE,
#       type=Property,
#       attributes=["apple is one of the most valueble companies in the world"],
#     ),
#     ChangeLog(
#       id=uuid4(), action=Action.CREATE, type=Edge, attributes=["apples ceo is tim cook"]
#     ),
#     ChangeLog(id=uuid4(), action=Action.UPDATE, type=Node, attributes=["tim cook"]),
#   ]
#   docs, ids, metadata, ids_to_delete = prepare_sync_data(, level)
#   assert len(ids_to_delete) == 2
#   assert len(ids) == 4
#   assert docs[0] == "apple"
#   assert isinstance(metadata[3]["type"], Node)
from __future__ import annotations
