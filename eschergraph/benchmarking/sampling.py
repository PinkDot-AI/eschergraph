from __future__ import annotations

import random
from typing import TypeAlias

QA_Set: TypeAlias = dict[str, dict[str, list[dict[str, str]]]]
QA_Sample: TypeAlias = list[dict[str, str]]


def sample_proportional(qa_set: QA_Set, num_tune: int) -> tuple[QA_Sample, QA_Sample]:
  """Sample a set of set of test and tune questions.

  Questions are sampled at random from the set of available questions.

  Args:
    qa_set (QA_Set): The generated set of question-answer pairs.
    num_tune (int): The number of tune questions to sample.

  Returns:
    A tuple containing the tune questions and the test questions, in
    that order.
  """
  prep_qa: QA_Sample = []

  for chunk, qa in qa_set.items():
    for pair in qa["Q&A"]:
      pair["chunk"] = chunk
      prep_qa.append(pair)

  # Sample the tune questions by removing from the test_qa questions
  random.shuffle(prep_qa)

  return prep_qa[:num_tune], prep_qa[num_tune:]
