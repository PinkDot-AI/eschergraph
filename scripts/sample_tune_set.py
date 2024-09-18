from __future__ import annotations

from eschergraph.benchmarking.sampling import QA_Set
from eschergraph.benchmarking.sampling import sample_proportional
from eschergraph.benchmarking.utils import load
from eschergraph.benchmarking.utils import save
from eschergraph.config import QA_GENERATED
from eschergraph.config import QA_TEST
from eschergraph.config import QA_TUNE

"""Script used to sample a tune and a test question-answer set."""

if __name__ == "__main__":
  qa_set: QA_Set = load(QA_GENERATED)
  tune_qa, test_qa = sample_proportional(qa_set, 10)
  save(tune_qa, QA_TUNE)
  save(test_qa, QA_TEST)
