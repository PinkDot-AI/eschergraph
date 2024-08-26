from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.builder.build_pipeline import BuildPipeline

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


def integration_test_building():
  client = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI, api_key=openai_api_key)
  file_path = "test_files/test_file.pdf"
  t = time.time()
  builder = BuildPipeline(
    file_location=file_path,
    model=client,
  )

  builder.run()
  print("processing time", time.time() - t)
  print(builder.graph.repository.get_all_at_level(0))
