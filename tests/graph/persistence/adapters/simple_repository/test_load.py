from __future__ import annotations

from pathlib import Path
from uuid import UUID

from eschergraph.graph import Edge
from eschergraph.graph import Node
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from tests.graph.help import create_simple_extracted_graph
from tests.graph.persistence.adapters.simple_repository.help import (
  compare_edge_to_edge_model,
)
from tests.graph.persistence.adapters.simple_repository.help import (
  compare_node_to_node_model,
)


def test_full_graph_loading(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  _, nodes, edges = create_simple_extracted_graph(repository=repository)
  node_ids_repository: set[UUID] = set(repository.nodes.keys())
  document_id: UUID = next(iter(nodes[0].metadata)).document_id

  assert node_ids_repository == {node.id for node in nodes}
  assert set(repository.edges.keys()) == {edge.id for edge in edges}
  assert set(repository.node_name_index.keys()) == {document_id}
  assert node_ids_repository == set(repository.node_name_index[document_id].values())

  repository.save()
  del repository

  new_repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  for node in nodes:
    new_node: Node = Node(id=node.id, repository=new_repository)
    assert new_node.loadstate == LoadState.REFERENCE
    assert compare_node_to_node_model(
      node=new_node,
      node_model=new_repository.nodes[node.id],
    )
    assert new_node.loadstate == LoadState.FULL  # type: ignore

  for edge in edges:
    new_edge: Edge = Edge(
      id=edge.id,
      frm=Node(edge.frm.id, repository=new_repository),
      to=Node(edge.to.id, repository=new_repository),
      repository=new_repository,
    )
    assert new_edge.loadstate == LoadState.REFERENCE
    assert compare_edge_to_edge_model(
      edge=new_edge, edge_model=new_repository.edges[edge.id]
    )
    assert new_edge.loadstate == LoadState.CORE  # type: ignore
