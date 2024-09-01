from __future__ import annotations

import random
from pathlib import Path
from typing import Optional
from uuid import UUID
from uuid import uuid4

from faker import Faker

from eschergraph.builder.build_log import BuildLog
from eschergraph.builder.build_log import EdgeExt
from eschergraph.builder.build_log import NodeExt
from eschergraph.builder.build_log import PropertyExt
from eschergraph.graph.persistence.adapters.simple_repository import SimpleRepository
from eschergraph.graph.persistence.metadata import Metadata

faker: Faker = Faker()


def create_build_logs(num_logs: Optional[int] = None) -> list[BuildLog]:
  build_logs: list[BuildLog] = []

  if not num_logs:
    num_logs = random.randint(1, 25)

  document_id: UUID = uuid4()

  for i in range(num_logs):
    metadata: Metadata = Metadata(document_id=document_id, chunk_id=i)

    nodes: list[NodeExt] = []
    edges: list[EdgeExt] = []
    properties: list[PropertyExt] = []

    for _ in range(random.randint(5, 20)):
      nodes.append({
        "name": faker.name(),
        "description": faker.text(max_nb_chars=120),
      })

    for _ in range(random.randint(15, 60)):
      edges.append({
        "source": faker.name(),
        "target": faker.name(),
        "relationship": faker.text(max_nb_chars=80),
      })

    for _ in range(random.randint(15, 60)):
      properties.append({
        "entity_name": faker.name(),
        "properties": [
          faker.text(max_nb_chars=40) for _ in range(random.randint(5, 15))
        ],
      })

    build_logs.append(
      BuildLog(
        metadata=metadata,
        properties=properties,
        edges=edges,
        nodes=nodes,
        chunk_text=faker.text(max_nb_chars=240),
      )
    )

  return build_logs


def test_original_building_logs_add_get(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  build_logs: list[BuildLog] = create_build_logs()
  document_id: UUID = build_logs[0].metadata.document_id

  assert repository.original_build_logs == dict()

  repository.add_original_build_logs(build_logs)

  assert (
    repository.get_original_build_logs_by_document_id(document_id=document_id)
    == build_logs
  )
  assert repository.original_build_logs[document_id] == build_logs


def test_original_building_logs_get_does_not_exist(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  assert repository.get_original_build_logs_by_document_id(uuid4()) == []


def test_original_building_logs_overwrite(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  list1, list2 = create_build_logs(), create_build_logs()
  doc1_id, doc2_id = list1[0].metadata.document_id, list2[0].metadata.document_id

  repository.add_original_build_logs(list1 + list2)

  assert repository.get_original_build_logs_by_document_id(doc1_id) == list1
  assert repository.get_original_build_logs_by_document_id(doc2_id) == list2

  list1_new, list2_new = create_build_logs(), create_build_logs()
  for log in list1_new:
    log.metadata.document_id = doc1_id
  for log in list2_new:
    log.metadata.document_id = doc2_id

  repository.add_original_build_logs(list2_new + list1_new)

  assert repository.get_original_build_logs_by_document_id(doc1_id) == list1_new
  assert repository.get_original_build_logs_by_document_id(doc2_id) == list2_new


def test_original_building_logs_get_all(saved_graph_dir: Path) -> None:
  repository: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )
  list1, list2, list3 = create_build_logs(), create_build_logs(), create_build_logs()

  repository.add_original_build_logs(list1 + list2 + list3)

  # Check that the results were saved as expected
  doc1_id: UUID = list1[0].metadata.document_id
  doc2_id: UUID = list2[0].metadata.document_id
  doc3_id: UUID = list3[0].metadata.document_id

  assert repository.original_build_logs == {
    doc1_id: list1,
    doc2_id: list2,
    doc3_id: list3,
  }

  repository.save()
  del repository
  new_repo: SimpleRepository = SimpleRepository(
    save_location=saved_graph_dir.as_posix()
  )

  original_building_logs: list[BuildLog] = new_repo.get_all_original_building_logs()

  assert len(list1 + list2 + list3) == len(original_building_logs)
  assert all(log in original_building_logs for log in list1)
  assert all(log in original_building_logs for log in list2)
  assert all(log in original_building_logs for log in list3)
