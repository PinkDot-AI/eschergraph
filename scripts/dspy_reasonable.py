from __future__ import annotations

from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

import dspy

from eschergraph.benchmarking.utils import load
from eschergraph.config import CHUNK_FILE
from eschergraph.config import QA_TEST

COMPILED_SAVE_PATH: str = "./eschergraph_storage/compiled.json"


class AccuracyScore(dspy.Signature):
  """Determine the reasonableness of an answer."""

  question = dspy.InputField()
  chunk = dspy.InputField(
    desc="The context from which the question-answer has been generated"
  )
  reference_answer = dspy.InputField(desc="The reference answer")
  answer = dspy.InputField(desc="The answer to score based on accuracy")
  score = dspy.OutputField(desc="Output only the score between 1 and 5")


class Evaluator(dspy.Module):
  """The evaluator class that score the reasonableness of an answer."""

  def __init__(self):
    """Initialize the Evaluator."""
    super().__init__()

    self.score = dspy.Predict(AccuracyScore)

  def forward(self, question: str, chunk: str, reference_answer: str, answer: str):
    """Generate an accuracy score."""
    score = self.score(
      question=question, chunk=chunk, reference_answer=reference_answer, answer=answer
    )
    return dspy.Prediction(answer=score.score)


def validate_score(example, pred, trace=None) -> int | bool:
  """The metric for the DSPy pipeline."""
  try:
    score: int = int(pred.answer)
  except ValueError:
    return 0

  score: int = abs(example.accuracy - score)
  if trace:
    return score == 0
  return 5 - score


if __name__ == "__main__":
  o_mini = dspy.OpenAI(model="gpt-4o")

  # Configure this as the default LM
  dspy.configure(lm=o_mini)

  # Load all the required data
  qa_set: list[dict[str, str]] = load(QA_TEST)
  chunks: dict[str, str] = load(CHUNK_FILE)
  pair: dict[str, str] = qa_set[0]

  # Construct the Example dataset
  # examples: list[dspy.Example] = []
  # for pair in qa_set:
  #   examples.append(
  #     dspy.Example(
  #       question=pair["question"],
  #       chunk=chunks[pair["chunk"]],
  #       reference_answer=pair["answer"],
  #       answer=pair["model_answer"],
  #       accuracy=int(pair["accuracy"]),
  #     ).with_inputs("question", "chunk", "reference_answer", "answer")
  #   )

  # Start by evluating the uncompiled program
  # evaluate = Evaluate(devset=examples, metric=validate_score, num_threads=4, display_progress=True, display_table=0)
  # evaluate(Evaluator())

  # config = dict(max_bootstrapped_demos=4, max_labeled_demos=4)
  # teleprompter = BootstrapFewShot(metric=validate_score, **config)
  # optimized_program = teleprompter.compile(Evaluator(), trainset=examples)
  # optimized_program.save(COMPILED_SAVE_PATH)
  optimized_evaluator = Evaluator()
  optimized_evaluator.load(COMPILED_SAVE_PATH)
  num_questions: int = len(qa_set)
  score: int = 0

  with ThreadPoolExecutor(max_workers=10) as executor:
    accuracy = {
      executor.submit(
        optimized_evaluator.forward,
        pair["question"],
        chunks[pair["chunk"]],
        pair["answer"],
        pair["model_answer"],
      )
      for pair in qa_set
    }
    for future in as_completed(accuracy):
      try:
        print(future.result().answer)
        score += int(future.result().answer.split()[-1])
      except ValueError:
        num_questions -= 1

  print("The results: ")
  print(f"The number of questions: {num_questions}")
  print(f"The average accuracy score: {score / num_questions}")
