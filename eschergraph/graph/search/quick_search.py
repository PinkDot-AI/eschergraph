# from eschergraph.graph import Graph
# from eschergraph.agents.reranker import Reranker
# from eschergraph.agents.providers.jina import JinaReranker
# from eschergraph.agents.providers.jina import JinaRerankerTurbo
# def search(Graph:Graph, query:str, open_source=False, max_prompt_size_tokens:int=800):
#     if open_source:
#         reranker:Reranker = JinaRerankerTurbo()
#     else:
#         reranker:Reranker = JinaReranker()
#     objects = search_objects(
#         Graph=Graph,
#         query=query,
#         reranker=reranker,
#         open_source=open_source,
#     )
#     #put objects in prompt en send to openai for RAG
#     pass
# def search_objects(Graph:Graph, query:str, reranker:Reranker, open_source:bool):
#     relevant_nodes = _get_relevant_nodes(
#         Graph=Graph,
#         query=query,
#         reranker = reranker,
#         open_source = open_source,
#     )
#     pass
# def _get_relevant_nodes(Graph:Graph, query:str, top_n:int = 20):
#     pass
from __future__ import annotations
