from __future__ import annotations

from eschergraph.builder.reader.reader import Reader

path = "test_files/Attention Is All You Need.pdf"

r = Reader(file_location=path, multimodal=True)
r.parse()
