from __future__ import annotations

from pathlib import Path

from eschergraph.tools.fast_pdf_parser.parser import FastPdfParser


def test_fast_pdf_parser() -> None:
  FastPdfParser.parse(
    Path.cwd().as_posix() + "/test_files/Attention Is All You Need.pdf"
  )
