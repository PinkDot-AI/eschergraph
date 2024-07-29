from __future__ import annotations

from random import randrange
from uuid import uuid4

from eschergraph.graph.persistence import Metadata


def create_metadata() -> Metadata:
  return Metadata(document_id=uuid4(), chunk_id=randrange(start=0, stop=int(1e6)))


def test_hash_metadata() -> None:
  assert isinstance(hash(create_metadata()), int)


def test_hash_metadata_unequal() -> None:
  assert hash(create_metadata()) != hash(create_metadata())
