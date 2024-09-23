from __future__ import annotations

from eschergraph import OpenAIModel
from eschergraph import OpenAIProvider
from eschergraph.agents.llm import ModelProvider
from eschergraph.builder.build_pipeline import BuildPipeline
from eschergraph.builder.reader import Reader

TEST_FILE_LOCATION: str = "./test_files/Attention Is All You Need.pdf"

if __name__ == "__main__":
  # The model used for obtaining a summary
  model: ModelProvider = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)

  # Read the test document
  reader: Reader = Reader(file_location=TEST_FILE_LOCATION)
  reader.parse()

  summary: str = BuildPipeline._get_summary(model, full_text=reader.full_text)

  print(summary)

  # Check whether a summary has been provided
  assert summary
