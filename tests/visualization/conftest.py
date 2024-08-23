from __future__ import annotations

import random

import pytest
from faker import Faker

faker: Faker = Faker()


@pytest.fixture(scope="function")
def node_name_comms() -> list[list[str]]:
  name_comms: list[list[str]] = []
  num_comms: int = 15
  for _ in range(num_comms):
    num_nodes: int = random.randint(3, 25)
    name_comms.append([faker.name() for _ in range(num_nodes)])

  return name_comms
