from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dotenv import load_dotenv

from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from eschergraph.benchmarking.sampling import QA_Sample
from eschergraph.benchmarking.utils import load
from eschergraph.config import CHUNK_FILE
from eschergraph.config import QA_TEST
from scripts.synthetic_qa import QA_SAVED

load_dotenv()

EVAL_RETRIEVAL: str = "retrieval_check.jinja"
ACCURACY_CHECK: str = "accuracy_check.jinja"
COMPLETE_CHECK: str = "complete_check.jinja"
REASONABLE_CHECK: str = "reasonable_check.jinja"

qa_set = dict[str, dict[str, dict[str, str]]]


def load_qa() -> dict[str, Any]:
  """Load the question and answer dataset."""
  return load(QA_SAVED)


def gpt_evaluation(
  qa_pair: dict[str, str],
  model: ModelProvider,
  prompt_location: str,
  chunks: dict[str, str],
) -> str:
  """Evaluate the answer with an LLM."""
  check_prompt: str = process_template(
    prompt_location,
    data={
      "question": qa_pair["question"],
      "reference_answer": qa_pair["answer"],
      "answer": qa_pair["model_answer"],
      "chunk": chunks[qa_pair["chunk"]],
    },
  )
  return model.get_plain_response(check_prompt)


if __name__ == "__main__":
  test_qa: QA_Sample = load(QA_TEST)
  chunks: dict[str, str] = load(CHUNK_FILE)

  # Possible to use either Groq or OpenAI
  model: ModelProvider = OpenAIProvider(model=OpenAIModel.GPT_4o)
  # model: ModelProvider = GroqProvider(model=GroqModel.LLAMA3_1_8B)

  num_questions: int = len(test_qa)
  acc_score: int = 0
  reas_score: int = 0
  comp_score: int = 0

  with ThreadPoolExecutor(max_workers=10) as executor:
    accuracy = {
      executor.submit(
        gpt_evaluation, qa_pair, model, ACCURACY_CHECK, chunks
      ): "accuracy"
      for qa_pair in test_qa
    }
    complete = {
      executor.submit(
        gpt_evaluation, qa_pair, model, COMPLETE_CHECK, chunks
      ): "complete"
      for qa_pair in test_qa
    }
    reasonable = {
      executor.submit(
        gpt_evaluation, qa_pair, model, REASONABLE_CHECK, chunks
      ): "reasonable"
      for qa_pair in test_qa
    }
    # Merge both dictionaries into a single list of futures
    all_futures = {**accuracy, **complete, **reasonable}

    # Collect all the results for labelling
    for future in as_completed(all_futures):
      score: int = int(future.result())
      if all_futures[future] == "accuracy":
        acc_score += score
      elif all_futures[future] == "complete":
        comp_score += score
      elif all_futures[future] == "reasonable":
        reas_score += score

  print("The results")
  print(f"The number of questions: {num_questions}")
  print(f"The accuracy: {acc_score / num_questions}")
  print(f"The completeness: {comp_score / num_questions}")
  print(f"The reasonablenes: {reas_score / num_questions}")
