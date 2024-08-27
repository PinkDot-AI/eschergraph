# from __future__ import annotations
# from uuid import uuid4
# from eschergraph.agents.providers.openai import OpenAIModel
# from eschergraph.agents.providers.openai import OpenAIProvider
# from eschergraph.graph.build_pipeline import Build
# from eschergraph.graph.build_pipeline import BuildLogItem
# from eschergraph.graph.graph import Graph
# from eschergraph.graph.persistence.metadata import Metadata
# from eschergraph.tools.reader import Chunk
# def test_build_pipeline() -> None:
#   openai = OpenAIProvider(
#     model=OpenAIModel.GPT_4o_MINI,
#     api_key="",
#   )
#   builder = Build(file_location="test_file.pdf", model=openai)
#   chunks: list[Chunk] = [
#     Chunk(
#       text="Tim Cooke is the CEO of Apple!",
#       chunk_id=1,
#       doc_id=uuid4(),
#       page_num=None,
#       doc_name="Mock_doc",
#     ),
#     Chunk(
#       text="Mock chunk 2",
#       chunk_id=1,
#       page_num=None,
#       doc_id=uuid4(),
#       doc_name="Mock_doc",
#     ),
#   ]
#   builder._handle_chunk_building(chunks[0])
# # def test_properties() -> None:
# #   test_log = BuildLogItem(
# #     chunk="Apple has many employees",
# #     metadata=Metadata(document_id=uuid4(), chunk_id=18),
# #     properties_json=None,
# #     node_edge_json={
# #       "entities": [
# #         {"name": "Apple", "description": "Apple is a company famous for the Iphone"}
# #       ],
# #       "relationships": [],
# #     },
# #   )
# #   openai = OpenAIProvider(
# #     model=OpenAIModel.GPT_4o_MINI,
# #   )
# #   builder = Build(file_location="test_file.pdf", model=openai)
# #   builder.building_logs.append(test_log)
# #   builder.graph = Graph('name')
# #   builder.graph.add_node(
# #     name= 'apple',
# #     description='apple is a company famous for the Iphone',
# #     metadata=Metadata(document_id=uuid4(), chunk_id=17),
# #     level = 0
# #   )
# #   builder
# #   for item in builder.building_logs:
# #     builder._handle_property_chunk(item)
# #   assert builder.building_logs[0].properties_json is not None
from __future__ import annotations

