from __future__ import annotations

import dspy

from eschergraph.benchmarking.utils import load
from eschergraph.config import CHUNK_FILE
from eschergraph.config import QA_TUNE


class ReasonableScore(dspy.Signature):
  """Determine the reasonableness of an answer."""

  question = dspy.InputField()
  chunk = dspy.InputField(
    desc="The context from which the question-answer has been generated"
  )
  reference_answer = dspy.InputField(desc="The reference answer")
  answer = dspy.InputField(desc="The answer to score based on reasonableness")
  score = dspy.OutputField(desc="The score on a scale of 1 to 5")


class Evaluator(dspy.Module):
  """The evaluator class that score the reasonableness of an answer."""

  def __init__(self):
    """Initialize the Evaluator."""
    super().__init__()

    self.score = dspy.ChainOfThought(ReasonableScore)

  def forward(self, question: str, chunk: str, reference_answer: str, answer: str):
    """Generate a reasonableness score."""
    score = self.score(
      question=question, chunk=chunk, reference_answer=reference_answer, answer=answer
    )
    return dspy.Prediction(answer=score.score)


if __name__ == "__main__":
  o_mini = dspy.OpenAI(model="gpt-4o-mini")

  # Configure this as the default LM
  dspy.configure(lm=o_mini)

  # Load all the required data
  qa_set: list[dict[str, str]] = load(QA_TUNE)
  chunks: dict[str, str] = load(CHUNK_FILE)
  pair: dict[str, str] = qa_set[0]

  print(
    Evaluator()
    .forward(
      question=pair["question"],
      chunk=chunks[pair["chunk"]],
      reference_answer=pair["answer"],
      answer=pair["model_answer"],
    )
    .answer
  )
