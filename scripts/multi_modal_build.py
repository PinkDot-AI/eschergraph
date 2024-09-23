from __future__ import annotations

from eschergraph.agents.providers.jina import JinaReranker
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.builder.reader.reader import Reader

builder = BuildPipeline(
  model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI), reranker=JinaReranker()
)

path = "test_files/Attention Is All You Need.pdf"

r = Reader(file_location=path, multimodal=True)
r.parse()


builder._handle_multi_modal(r.visual_elements)
