from __future__ import annotations

from faker import Faker

from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.agents.providers.openai import OpenAIProvider
from tests.conftest import provider_test

faker: Faker = Faker()


@provider_test
def test_openai_embedding_call() -> None:
  embedding_provider: OpenAIProvider = OpenAIProvider(
    model=OpenAIModel.TEXT_EMBEDDING_LARGE
  )
  text_list: list[str] = [faker.text(max_nb_chars=120) for _ in range(20)]
  embeddings: list[list[float]] = embedding_provider.get_embedding(text_list)
  assert embeddings
