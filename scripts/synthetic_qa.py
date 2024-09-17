from __future__ import annotations

import json
from typing import Any

from dotenv import load_dotenv

from eschergraph.agents import OpenAIModel
from eschergraph.agents import OpenAIProvider
from eschergraph.agents.jinja_helper import process_template
from eschergraph.tools.reader import Chunk
from eschergraph.tools.reader import Reader

load_dotenv()

TEST_FILE: str = "./test_files/Attention Is All You Need.pdf"
PROMPT_KEYWORDS: str = "keywords.jinja"
KEYWORDS_SAVED: str = "./eschergraph_storage/keywords.json"
QA_PROMPT: str = "questions.jinja"
QA_SAVED: str = "./eschergraph_storage/qa.json"
FILTER_PROMPT: str = "filter_questions.jinja"

model: OpenAIProvider = OpenAIProvider(model=OpenAIModel.GPT_4o)


def get_keywords(paper: str) -> dict[str, list[str]]:
  """Get all the keywords for the paper."""
  # Parse the entire file into a single chunk to extract the keywords
  reader: Reader = Reader(file_location=paper, optimal_tokens=6000)
  chunks: list[Chunk] = reader.parse()
  prompt: str = process_template(
    template_file=PROMPT_KEYWORDS, data={"paper": chunks[0].text}
  )
  return model.get_json_response(prompt=prompt)


def save(keywords: dict[str | int, Any], filename: str) -> None:
  """Save a JSON object to file."""
  with open(filename, "w") as file:
    json.dump(keywords, file, indent=4)


def load(filename: str) -> dict[str | int, Any]:
  """Load a JSON object to a dictionary."""
  with open(filename, "r") as file:
    keywords = json.load(file)
  return keywords


def get_retrieval_qa(filename, keywords) -> dict[int, Any]:
  """Get question-answer pairs for each chunk."""
  reader: Reader = Reader(file_location=filename)
  chunks: list[Chunk] = reader.parse()
  qa_doc: dict[int, Any] = {}
  for idx, chunk in enumerate(chunks):
    qa_prompt: str = process_template(
      template_file=QA_PROMPT,
      data={"keywords": keywords["keywords"], "paper_text": chunk.text},
    )
    qa_pairs: dict[str, list[dict[str, str]]] = model.get_json_response(
      prompt=qa_prompt
    )
    filter_prompt: str = process_template(
      template_file=FILTER_PROMPT,
      data={"paper_text": chunk.text, "qa_pairs": qa_pairs["Q&A"]},
    )
    qa_pairs = model.get_json_response(prompt=filter_prompt)
    qa_doc[idx] = qa_pairs

  return qa_doc


if __name__ == "__main__":
  # keywords: dict[str, list[str]] = get_keywords(TEST_FILE)
  # save(keywords, KEYWORDS_SAVED)
  # keywords: dict[str, list[str]] = load(KEYWORDS_SAVED)
  # qa_doc: dict[int, Any] = get_retrieval_qa(TEST_FILE)
  # save(qa_doc, QA_SAVED)
  print(get_keywords(TEST_FILE))
