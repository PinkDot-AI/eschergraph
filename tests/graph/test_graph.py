from __future__ import annotations

from eschergraph.graph import Graph


def test_default_creation() -> None:
  Graph(name="test_default_graph")
