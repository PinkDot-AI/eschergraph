from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from eschergraph import Graph
from eschergraph.agents.jinja_helper import process_template
from eschergraph.agents.llm import ModelProvider
from eschergraph.agents.providers.groq import GroqModel
from eschergraph.agents.providers.groq import GroqProvider
from eschergraph.graph.search.attribute_search import AttributeSearch
from eschergraph.graph.search.quick_search import quick_search
from scripts.evaluate_global_search import get_or_create_graph
from scripts.synthetic_qa import load
from scripts.synthetic_qa import QA_SAVED

load_dotenv()

EVAL_RETRIEVAL: str = "retrieval_check.jinja"
ANSWER_CHECK: str = "answer_check.jinja"

qa_set = dict[str, dict[str, dict[str, str]]]


def load_qa() -> qa_set:
  """Load the question and answer dataset."""
  return load(QA_SAVED)


def retrieval_top_for_question(
  chunk_idx: int, attributes: list[AttributeSearch]
) -> bool:
  """Get the retrieval results for a question.

  Assign correct if the relevant chunk as one of the top 3 most frequent.
  """
  chunk_frequency: dict[str, int] = {}
  # Update the chunk_frequency
  for attr in attributes:
    for md in attr.metadata:
      if md.chunk_id in chunk_frequency:
        chunk_frequency[str(md.chunk_id)] += 1
      else:
        chunk_frequency[str(md.chunk_id)] = 1

  # Sort the chunks that appear most often
  sorted_chunks: list[tuple[int, int]] = sorted(
    chunk_frequency.items(), key=lambda item: item[1], reverse=True
  )
  top_3: list[int] = [sc[0] for sc in sorted_chunks[:3]]

  if chunk_idx in top_3:
    return True
  return False


def gpt_evaluation(
  pair: dict[str, str], model: ModelProvider, graph: Graph
) -> dict[str, str]:
  """Evaluate the answer with an LLM."""
  answer: str = quick_search(graph, pair["question"])
  check_prompt: str = process_template(
    ANSWER_CHECK,
    data={
      "question": pair["question"],
      "reference_answer": pair["answer"],
      "answer": answer,
    },
  )
  score: dict[str, int] = model.get_json_response(check_prompt)

  return {"prompt": check_prompt, "answer": score}


if __name__ == "__main__":
  qa_data: qa_set = load_qa()

  # Get the graph for testing
  graph: Graph = get_or_create_graph()

  # Possible to use either Groq or OpenAI
  model: ModelProvider = GroqProvider(model=GroqModel.LLAMA_3_1_70B)
  # model: ModelProvider = OpenAIProvider(model=OpenAIModel.GPT_4o_MINI)

  # Keeping score
  num_questions: int = 0
  accuracy: int = 0
  complete: int = 0
  reasonable: int = 0
  pairs: list[tuple[dict[str, str], str]] = [
    (pair, chunk_idx)
    for chunk_idx in qa_data.keys()
    for pair in qa_data[chunk_idx]["Q&A"]
  ]

  with ThreadPoolExecutor(max_workers=2) as executor:
    gpt_check = {
      executor.submit(gpt_evaluation, pair[0], model, graph): "gpt" for pair in pairs
    }
    # Merge both dictionaries into a single list of futures
    all_futures = {**gpt_check}

    # Collect all the results for labelling
    for future in as_completed(all_futures):
      result = future.result()["answer"]

      if (
        not "accuracy" in result
        or not "completeness" in result
        or not "reasonableness" in result
      ):
        print("An error with the score!!")
        continue

      num_questions += 1
      accuracy += result["accuracy"]
      complete += result["completeness"]
      reasonable += result["reasonableness"]

  # To improve the benchmarking, consider using the CAR metric for the answers generated
  print("The results: ")
  print(f"The number of questions: {num_questions}")
  print(f"The average accuracy: {accuracy / num_questions}")
  print(f"The average completeness: {complete / num_questions}")
  print(f"The average reasonableness: {reasonable / num_questions}")
