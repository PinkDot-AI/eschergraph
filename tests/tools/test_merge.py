# from __future__ import annotations
# from uuid import uuid4
# from eschergraph.agents.providers.openai import OpenAIModel
# from eschergraph.agents.providers.openai import OpenAIProvider
# from eschergraph.build.buildlogsitem import BuildLogItem
# from eschergraph.graph.graph import Graph
# from eschergraph.graph.persistence.metadata import Metadata
# from eschergraph.tools.merge import Merge
# def test_merge():
#   merger: Merge = Merge(
#     model=OpenAIProvider(
#       model=OpenAIModel.GPT_4o_MINI,
#       api_key="",
#     )
#   )
#   test_buildinglogs: list[BuildLogItem] = [
#     BuildLogItem(
#       chunk="Sam Altman, the CEO and co-founder of OpenAI, has made significant strides in the AI industry, asserting that OpenAI will become the best AI company the world has ever seen. His leadership at OpenAI, a non-profit organization dedicated to advancing AI for the benefit of humanity, is widely recognized. Sam is also known for his impactful tenure as the president of Y Combinator, one of the most prestigious startup incubators globally. Despite his professional achievements, Sam Altman is noted for leading a personal life without children.s",
#       node_edge_json={
#         "entities": [
#           {"name": "sam altman", "description": "sam altman is the CEO of openai"},
#           {
#             "name": "sam",
#             "description": "sam says openai will be the best ai company the world has every seen",
#           },
#           {
#             "name": "openai",
#             "description": "openai is a non-profit company founded amogs other sam altman and are making ai for humankind.",
#           },
#           {
#             "name": "y combinator",
#             "description": "y combinator is one of the most famous start up schools in the world.",
#           },
#         ],
#         "relationships": [
#           {
#             "source": "sam altman",
#             "target": "openai",
#             "description": "sam altman is the ceo and co-found of openai.",
#           },
#           {
#             "source": "sam altman",
#             "target": "y combinator",
#             "description": "sam altman was the president of y combinator.",
#           },
#         ],
#       },
#       properties_json={
#         "sam": [
#           "sam is famous for the time as president of Y combinator",
#           "sam is does not have any children",
#         ],
#       },
#       metadata=Metadata(document_id=uuid4(), chunk_id=2),
#     ),
#     BuildLogItem(
#       chunk="Sam has become a prominent figure in the cryptocurrency industry, known for both his entrepreneurial success and the controversies surrounding his platform, FTX. As the founder and CEO of FTX, Sam has been deeply involved in shaping the crypto landscape. Often referred to as the poster boy of the crypto industry, his journey reflects both the potential and pitfalls of this emerging financial sector. Despite his achievements, his association with FTX's issues has sparked significant debate.",
#       node_edge_json={
#         "entities": [
#           {
#             "name": "sam bankman-fried",
#             "description": "sam bank-fried is an american entrepreneur infamous for his crypotocurrency fraud issues with FTX.",
#           },
#           {
#             "name": "ftx",
#             "description": "ftx is a crypo currency platform founded by sam bankman-fried",
#           },
#         ],
#         "relationships": [
#           {
#             "source": "sam",
#             "target": "ftx",
#             "description": "sam is the founder and ceo of ftx",
#           },
#         ],
#       },
#       properties_json={
#         "entities": [
#           {"entities": {"sam": ["sam is the poster boy of the crypto industry"]}}
#         ]
#       },
#       metadata=Metadata(document_id=uuid4(), chunk_id=3),
#     ),
#     BuildLogItem(
#       chunk="In a recent interview about AI, Sam, the primary subject, shared his insights on the evolving landscape of artificial intelligence. Described as someone deeply invested in the field, Sam highlighted various advancements while casually mentioning his personal quirks. Despite his deep involvement in AI, Sam doesn’t have any children and amusingly noted his fondness for cake. His light-hearted remarks added a unique flavor to the discussion, making the conversation both informative and engaging.",
#       node_edge_json={
#         "entities": [
#           {
#             "name": "sam",
#             "description": "sam is the one being interviewed about ai",
#           }
#         ],
#         "relationships": [],
#       },
#       properties_json={
#         "entities": [{"sam": ["sam does not have any children", "likes cake a lot"]}]
#       },
#       metadata=Metadata(document_id=uuid4(), chunk_id=4),
#     ),
#   ]
#   unique_node_names: list[str] = [
#     "sam",
#     "sam altman",
#     "sam bankman-fried",
#     "openai",
#     "ftx",
#     'y combinator'
#   ]
#   merger.merge(building_logs=test_buildinglogs, unique_node_names=unique_node_names)
from __future__ import annotations
