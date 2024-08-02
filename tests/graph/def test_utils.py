from __future__ import annotations

from eschergraph.graph.utils import _extract_property_type


def test_extract_property_type_string() -> None:
  assert _extract_property_type("list[str]") == ""
  assert _extract_property_type("Optional[int]") == "int"
  assert _extract_property_type("Optional[set[int]]") == "set[int]"
  assert _extract_property_type("") == ""
