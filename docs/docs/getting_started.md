---
sidebar_position: 1
---

# Getting started

Lets learn how to build, and RAGsearch with **EscherGraph** in under 5 min.

## Quick start

```bash
pip install eschergraph
```

For the graph building, a LLM and a reranker is needed. We recommond using GPT4o and the jina-reranker-v2-base-multilingual, these models are also defaulted.

First put your OpenAI and Jina api key in a .env file

```python
# .env file
OPENAI_API_KEY = ... 
JINA_API_KEY = ...
```
Jina AI has a 1 million free tokens on their platform, get it here https://jina.ai/embeddings/

### Initialize graph

```python
from eschergraph import Graph
#from eschergraph import OpenAIProvider, OpenAIModel

graph_name = 'pink graph'
graph = Graph(
    #model=OpenAIProvider(model=OpenAIModel.GPT_4o_MINI) # default model is GPT_4o
    name=graph_name,
  )
```
Currently are the available models GPT4o and GPT4o-mini. We recommond always using GPT4o for graph building. The GPT 4o-mini experiences too much variance on graph building. We recommend using GPT4o mini for playing around and testing.

### Build graph
```python
my_file1 = 'test_files/Attention Is All You Need.pdf'

graph.build(files = my_file1)

# Adding another file to the same graph, is possible by simply building again:
my_file2 = 'test_files/Test file2.pdf'

graph.build(files = my_file2)
```
Files takes one file location, or a list of file locations. Currently only .pdf or .txt files are available file types.

Graph building will take a while, dependent on the size of the files.

### Local RAG search
```python
question = 'On which hardware chips were the inital models trained?'

answer = graph.search(question)
print(answer)
```
Local search goes throught all, nodes, edges and properties to find the moest relevant answers using embedding similarity and reranking. 

### Global RAG search
```python
global_question = 'What are the conclusions from the paper?'

answer = graph.global_search(question)
print(answer)
```
Global search is search on the higher levels of the graph, and is great for answering general topic question about the files in the graph.

### Dashboard
```python
graph.dashboard()
```
Print general info and statistics about the graph using the dashboard.