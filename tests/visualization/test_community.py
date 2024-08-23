from __future__ import annotations

from eschergraph.visualization.community import _community_to_colors


def test_community_to_colors(node_name_comms: list[list[str]]) -> None:
  comm_colors: list[dict[str, str | int]] = _community_to_colors(node_name_comms)
  comm_color_code: list[set[str]] = [set() for _ in range(len(node_name_comms))]

  for node in comm_colors:
    comm_color_code[int(node["group"]) - 1].add(str(node["color"]))

  for comm_color in comm_color_code:
    assert len(comm_color) == 1

  assert comm_colors[-1]["group"] == len(node_name_comms)
