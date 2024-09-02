---
sidebar_position: 1
---

# File Parsing

### PDF files

Parsing PDF files can be challenging due to difficulties in extracting and chunking text accurately. For PDF files, EscherGraph utilizes an open-source document layout model developed by HURIDOCS (https://github.com/huridocs/pdf-document-layout-analysis), the LightGBM. This model leverages XML data extracted by Poppler for analysis.

We are actively working on enhancing EscherGraph to be multimodal. The VGT (Vision Grid Transformer) model from HURIDOCS will enable this advancement, only this model is too large to run on local device, and needs a GPU. 

For paragraph detection and chunking, we use their model within our parser function:

```python
from eschergraph.tools.reader import Reader, Chunk
file_location = 'test_files/Attention is All You Need.pdf'

reader = Reader(
    file_location: file_location
)
reader.parse()
chunks = reader.chunks -> list[Chunk]
```

Here is the Chunk object definition:

```python
@define
class Chunk:
  """The chunk object."""

  text: str
  chunk_id: int
  doc_id: UUID
  page_num: Optional[int]
  doc_name: str
```
### TXT files:
For TXT files, we use the Langchain recursive splitter, with a standard chunk size of 1500 characters and an overlap of 300 characters:
```python
from eschergraph.tools.reader import Reader
file_location = 'test_files/txt_file.txt'

reader = Reader(
    file_location = file_location,
    chunk_size = 1500,
    overlap = 300
)
reader.parse()
chunks = reader.chunks
```