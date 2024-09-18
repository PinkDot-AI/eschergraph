from __future__ import annotations

import os
from unittest.mock import patch
from uuid import uuid4

import pytest

from eschergraph.builder.reader.multi_modal.data_structure import Table
from eschergraph.builder.reader.multi_modal.multi_modal_parser import (
  _generate_markdown_table,
)
from eschergraph.builder.reader.multi_modal.multi_modal_parser import _handle_figures
from eschergraph.builder.reader.multi_modal.multi_modal_parser import _handle_tables


@pytest.fixture
def sample_table() -> Table:
  return {
    "column_count": 3,
    "row_count": 3,
    "cells": [
      {"row_index": 0, "column_index": 0, "content": "Header1"},
      {"row_index": 0, "column_index": 1, "content": "Header2"},
      {"row_index": 0, "column_index": 2, "content": "Header3"},
      {"row_index": 1, "column_index": 0, "content": "Row1Col1"},
      {"row_index": 1, "column_index": 1, "content": "Row1Col2"},
      {"row_index": 1, "column_index": 2, "content": "Row1Col3"},
      {"row_index": 2, "column_index": 0, "content": "Row2Col1"},
      {"row_index": 2, "column_index": 1, "content": "Row2Col2"},
      {"row_index": 2, "column_index": 2, "content": "Row2Col3"},
    ],
    "id": 0,
    "caption": "This is a caption",
    "page_num": 18,
    "bounding_regions": [{"page_number": 2, "polygon": [1.2, 2.2, 4.1, 2.1]}],
  }


@pytest.fixture
def empty_table() -> Table:
  return {
    "column_count": 2,
    "row_count": 2,
    "cells": [
      {"row_index": 0, "column_index": 0, "content": ""},
      {"row_index": 0, "column_index": 1, "content": ""},
      {"row_index": 1, "column_index": 0, "content": ""},
      {"row_index": 1, "column_index": 1, "content": ""},
    ],
    "id": 0,
    "caption": "This is a caption",
    "page_num": 18,
    "bounding_regions": [{"page_number": 2, "polygon": [1.2, 2.2, 4.1, 2.1]}],
  }


@pytest.fixture
def special_char_table() -> Table:
  return {
    "column_count": 2,
    "row_count": 2,
    "cells": [
      {"row_index": 0, "column_index": 0, "content": "Header!@#"},
      {"row_index": 0, "column_index": 1, "content": "Header$%^"},
      {"row_index": 1, "column_index": 0, "content": "Row*&1"},
      {"row_index": 1, "column_index": 1, "content": "Row()2"},
    ],
    "id": 0,
    "caption": "This is a caption",
    "page_num": 18,
    "bounding_regions": [{"page_number": 2, "polygon": [1.2, 2.2, 4.1, 2.1]}],
  }


# Test with normal data
def test_generate_markdown_table(sample_table) -> None:
  expected_markdown = (
    "| Header1 | Header2 | Header3 |\n"
    "| --- | --- | --- |\n"
    "| Row1Col1 | Row1Col2 | Row1Col3 |\n"
    "| Row2Col1 | Row2Col2 | Row2Col3 |\n"
  )
  markdown_result = _generate_markdown_table(sample_table)
  assert (
    markdown_result == expected_markdown
  ), f"Expected: {expected_markdown}, but got: {markdown_result}"


# Test with an empty table
def test_generate_markdown_empty_table(empty_table) -> None:
  expected_markdown = "|  |  |\n" "| --- | --- |\n" "|  |  |\n"
  markdown_result = _generate_markdown_table(empty_table)
  assert (
    markdown_result == expected_markdown
  ), f"Expected: {expected_markdown}, but got: {markdown_result}"


# Test with special characters in the table
def test_generate_markdown_special_char_table(special_char_table) -> None:
  expected_markdown = (
    "| Header!@# | Header$%^ |\n" "| --- | --- |\n" "| Row*&1 | Row()2 |\n"
  )
  markdown_result = _generate_markdown_table(special_char_table)
  assert (
    markdown_result == expected_markdown
  ), f"Expected: {expected_markdown}, but got: {markdown_result}"


# Edge case: Table with one row and one column
def test_generate_markdown_single_cell() -> None:
  table = {
    "column_count": 1,
    "row_count": 1,
    "cells": [{"row_index": 0, "column_index": 0, "content": "HeaderOnly"}],
  }
  expected_markdown = "| HeaderOnly |\n" "| --- |\n"
  markdown_result = _generate_markdown_table(table)
  assert (
    markdown_result == expected_markdown
  ), f"Expected: {expected_markdown}, but got: {markdown_result}"


# Edge case: Table with multiple empty rows
def test_generate_markdown_empty_rows() -> None:
  table = {
    "column_count": 3,
    "row_count": 3,
    "cells": [
      {"row_index": 0, "column_index": 0, "content": "Header1"},
      {"row_index": 0, "column_index": 1, "content": "Header2"},
      {"row_index": 0, "column_index": 2, "content": "Header3"},
      {"row_index": 1, "column_index": 0, "content": ""},
      {"row_index": 1, "column_index": 1, "content": ""},
      {"row_index": 1, "column_index": 2, "content": ""},
      {"row_index": 2, "column_index": 0, "content": "Row2Col1"},
      {"row_index": 2, "column_index": 1, "content": ""},
      {"row_index": 2, "column_index": 2, "content": "Row2Col3"},
    ],
  }
  expected_markdown = (
    "| Header1 | Header2 | Header3 |\n"
    "| --- | --- | --- |\n"
    "|  |  |  |\n"
    "| Row2Col1 |  | Row2Col3 |\n"
  )
  markdown_result = _generate_markdown_table(table)
  assert (
    markdown_result == expected_markdown
  ), f"Expected: {expected_markdown}, but got: {markdown_result}"


def test_handle_tables() -> None:
  # Mock data
  doc_id = uuid4()
  file_location = "test_file.pdf"
  base_name = os.path.basename(file_location)
  output_folder = os.path.join("eschergraph_storage", base_name)
  tables_folder = os.path.join(output_folder, "tables")

  analysis_results = {
    "tables": [
      {
        "caption": "Sample Table",
        "bounding_regions": [{"top": 0, "left": 0, "width": 100, "height": 100}],
        "page_num": 1,
      }
    ]
  }

  expected_cropped_image_filename = "mocked_image_path.png"
  expected_markdown_table = "| Column |"

  # Patching the functions `_generate_markdown_table` and `_save_cropped_image`
  with patch(
    "eschergraph.builder.reader.multi_modal.multi_modal_parser._generate_markdown_table",
    return_value=expected_markdown_table,
  ):
    with patch(
      "eschergraph.builder.reader.multi_modal.multi_modal_parser._save_cropped_image",
      return_value=expected_cropped_image_filename,
    ):
      # Run the function
      visual_elements = _handle_tables(
        analysis_results, tables_folder, doc_id, file_location
      )

      # Assertions
      assert len(visual_elements) == 1  # Only one table in the analysis_results
      v = visual_elements[0]
      assert v.caption == "Sample Table"
      assert v.page_num == 1
      assert v.save_location == expected_cropped_image_filename
      assert v.content == f"{v.caption}\n{expected_markdown_table}"


def test_handle_figures() -> None:
  # Mock data
  doc_id = uuid4()
  file_location = "test_file.pdf"
  base_name = os.path.basename(file_location)
  output_folder = os.path.join("eschergraph_storage", base_name)
  figures_folder = os.path.join(output_folder, "figures")

  analysis_results = {
    "figures": [
      {
        "caption": "Sample Figure",
        "bounding_regions": [{"top": 0, "left": 0, "width": 200, "height": 200}],
        "page_num": 2,
      }
    ]
  }

  expected_cropped_image_filename = "mocked_figure_image_path.png"

  # Patching the function `_save_cropped_image`
  with patch(
    "eschergraph.builder.reader.multi_modal.multi_modal_parser._save_cropped_image",
    return_value=expected_cropped_image_filename,
  ):
    # Run the function
    visual_elements = _handle_figures(
      analysis_results, figures_folder, doc_id, file_location
    )

    # Assertions
    assert len(visual_elements) == 1  # Only one figure in the analysis_results
    v = visual_elements[0]
    assert v.caption == "Sample Figure"
    assert v.page_num == 2
    assert v.save_location == expected_cropped_image_filename
    assert v.content == ""  # No content for figures in this case
    assert v.type == "FIGURE"
