from __future__ import annotations

import pytest

from eschergraph.graph.base import EscherBase
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence import Repository
from eschergraph.graph.utils import _extract_property_type
from eschergraph.graph.utils import loading_getter_setter


@pytest.fixture(scope="function")
def base_repository(mock_repository: Repository) -> Repository:
  # Set the metadata equal to an empty set
  def load_side_effect(base: EscherBase, loadstate: LoadState) -> None:
    base._metadata = set()

  mock_repository.load.side_effect = load_side_effect  # type: ignore

  return mock_repository


def test_extract_property_type_string() -> None:
  assert _extract_property_type("list[str]") == ""
  assert _extract_property_type("Optional[int]") == "int"
  assert _extract_property_type("Optional[set[int]]") == "set[int]"
  assert _extract_property_type("") == ""


# Testing whether the class decorator works.
# Note that it cannot be applied to the base class directly as that would
# trigger a circular import.
@loading_getter_setter
class ExtendedBase(EscherBase): ...


def test_check_loadstate_metadata(base_repository: Repository) -> None:
  base: EscherBase = ExtendedBase(repository=base_repository)

  assert isinstance(base.metadata, set)
  assert base.loadstate == LoadState.CORE
