from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

from eschergraph.graph.base import EscherBase
from eschergraph.graph.community import Community
from eschergraph.graph.loading import LoadState
from eschergraph.graph.utils import _extract_inner_type
from eschergraph.graph.utils import _extract_property_type
from eschergraph.graph.utils import _parse_future_annotations
from eschergraph.graph.utils import loading_getter_setter
from eschergraph.persistence import Metadata


@pytest.fixture(scope="function")
def base_repository(mock_repository: Mock) -> Mock:
  # Set the metadata equal to an empty set
  def load_side_effect(base: EscherBase, loadstate: LoadState) -> None:
    base._metadata = set()

  mock_repository.load.side_effect = load_side_effect

  return mock_repository


def test_extract_property_type_string() -> None:
  assert _extract_property_type("list[str]") == ""
  assert _extract_property_type("Optional[int]") == "int"
  assert _extract_property_type("Optional[set[int]]") == "set[int]"
  assert _extract_property_type("") == ""


def test_extract_inner_type() -> None:
  assert _extract_inner_type("") == ""
  assert _extract_inner_type("list[str]") == ""
  assert _extract_inner_type("Optional[set[int]]") == "set"
  assert _extract_inner_type("Optional[Node]") == "Node"


def test_parse_future_annotations() -> None:
  with pytest.raises(RuntimeError):
    _parse_future_annotations("")
    _parse_future_annotations("list[str]")

  _parse_future_annotations("Optional[set[int]]") == set
  _parse_future_annotations("Optional[list[str]]") == list
  _parse_future_annotations("Optional[Community]") == Community


# Testing whether the class decorator works.
# Note that it cannot be applied to the base class directly as that would
# trigger a circular import.
@loading_getter_setter
class ExtendedBase(EscherBase): ...


def test_check_loadstate_metadata(base_repository: Mock) -> None:
  base: EscherBase = ExtendedBase(repository=base_repository)

  assert isinstance(base.metadata, set)
  assert base.loadstate == LoadState.CORE


def test_setting_metadata(base_repository: Mock) -> None:
  base: EscherBase = ExtendedBase(repository=base_repository)

  metadata_set: set[Metadata] = {Metadata(document_id=uuid4(), chunk_id=1)}
  assert not base._metadata
  assert base.loadstate == LoadState.REFERENCE

  base.metadata = metadata_set

  assert base.metadata == metadata_set
  assert base.loadstate == LoadState.CORE  # type: ignore
