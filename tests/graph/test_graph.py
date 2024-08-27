from __future__ import annotations

from eschergraph.graph import Graph


# TODO: remove this test as no logic is tested
def test_default_creation(graph_unit: Graph) -> None:
  assert isinstance(graph_unit, Graph)
