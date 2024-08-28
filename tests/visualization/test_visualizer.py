from __future__ import annotations

import os
import webbrowser
from unittest.mock import MagicMock

from pytest import MonkeyPatch

from eschergraph.graph import Edge
from eschergraph.graph import Graph
from eschergraph.graph import Node
from eschergraph.visualization import Visualizer


def test_visualize_graph(
  visualization_dir: str,
  graph_visual: tuple[Graph, list[Node], list[Edge]],
  monkeypatch: MonkeyPatch,
) -> None:
  graph, nodes, _ = graph_visual
  graph.repository.get_all_at_level.return_value = nodes

  mock_open_browser: MagicMock = MagicMock()
  monkeypatch.setattr(webbrowser, "open", mock_open_browser)

  html_path: str = visualization_dir + "/graph_visual.html"
  Visualizer.visualize_graph(graph=graph, level=0, save_location=html_path)

  mock_open_browser.assert_called_once()
  assert os.path.exists(html_path)


def test_visualize_community_graph(
  community_graph: tuple[list[list[Node]], list[Edge]],
  visualization_dir: str,
  monkeypatch: MonkeyPatch,
) -> None:
  mock_open_browser: MagicMock = MagicMock()

  monkeypatch.setattr(webbrowser, "open", mock_open_browser)

  html_path: str = visualization_dir + "/community_visual.html"
  Visualizer.visualize_community_graph(
    comms=community_graph[0],
    edges=community_graph[1],
    save_location=html_path,
  )

  mock_open_browser.assert_called_once()
  assert os.path.exists(html_path)
