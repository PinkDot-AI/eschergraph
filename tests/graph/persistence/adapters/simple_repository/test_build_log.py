from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from faker import Faker

from eschergraph.builder.build_log import BuildLog
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository

faker: Faker = Faker()


def get_build_logs(num_logs: Optional[int] = None) -> list[BuildLog]:
  if not num_logs:
    num_logs = random.randint(1, 25)
  ...


def test_original_building_logs_add(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
