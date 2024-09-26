from __future__ import annotations

from eschergraph.agents import OpenAIModel
from eschergraph.agents import OpenAIProvider
from eschergraph.graph import Graph
from eschergraph.visualization.visualizer import Visualizer

TEST_DOCUMENT: str = "./test_files/Attention Is All You Need.pdf"


# Watch out! Running this may incur costs for building the graph
def get_or_create_graph() -> Graph:
  """Get or build the graph needed for the evaluation."""
  graph: Graph = Graph(
    name="eval_global_search", model=OpenAIProvider(model=OpenAIModel.GPT_4o)
  )

  # Check if the test file has already been added to the graph
  if graph.repository.get_all_at_level(0):
    return graph

  graph.build(TEST_DOCUMENT)
  return graph


if __name__ == "__main__":
  graph: Graph = get_or_create_graph()
  Visualizer.visualize_graph(graph, level=1)
  print([
    prop.description for prop in graph.repository.get_all_at_level(2)[0].properties
  ])
  # print(graph.global_search("What is the point of a transformer architecture?"))
  # print(graph.search("How to measure proficiency in translation tasks?"))
