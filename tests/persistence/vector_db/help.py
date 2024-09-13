from __future__ import annotations

import random
from uuid import UUID
from uuid import uuid4

from faker import Faker

from eschergraph.persistence.vector_db import VectorSearchResult

faker: Faker = Faker()


def generate_insert_data(
  num_docs: int = 10,
) -> tuple[list[str], list[UUID], list[dict[str, str | int]]]:
  docs: list[str] = [faker.text(max_nb_chars=80) for _ in range(num_docs)]
  ids: list[UUID] = [uuid4() for _ in range(num_docs)]
  metadatas: list[dict[str, str | int]] = [
    {
      "level": random.randint(0, 10),
      "type": random.choice(["node", "edge", "property"]),
      "document_id": str(uuid4()),
    }
    for _ in range(num_docs)
  ]

  return docs, ids, metadatas


def generate_vector_search_results(num_results: int = 10) -> list[VectorSearchResult]:
  return [
    VectorSearchResult(
      id=uuid4(),
      chunk=faker.text(max_nb_chars=80),
      type=random.choice(["node", "edge", "property"]),
      distance=random.random(),
    )
    for _ in range(num_results)
  ]
