from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

from eschergraph.agents.providers.openai import ChatGPT
from eschergraph.agents.providers.openai import OpenAIModel
from eschergraph.exceptions import ExternalProviderException
from eschergraph.graph.persistence.vector_db.providers.chromadb import ChromaDB
from eschergraph.graph.persistence.vector_db.vector_db import VectorDB
from eschergraph.graph.search.quick_search import search

load_dotenv()


def test_search() -> None:
  # Initialize vector database
  vectordb: VectorDB = ChromaDB()
  collection_name: str = "test_collection"
  vectordb.create_collection(collection_name)

  api_key = os.getenv("OPENAI_API_KEY")
  if api_key:
    llm = ChatGPT(model=OpenAIModel.GPT_4o_MINI, api_key=api_key)
  else:
    raise ExternalProviderException("missing openai ai apikey")

  # Combined lists of documents, embeddings, and metadata
  documents: list[str] = [
    "apple",
    "microsoft",
    "amazon",
    "sam altman",
    "apple and microsoft are part of the magnificent seven",
    "microsoft has a partnership with sam altman",
    "amazon is a software and logistics company",
    "sam altman is a famous entrepreneur",
    "sam altman is a vegetarian",
  ]

  metadatas: list[dict[str, Any]] = [
    {
      "level": 0,
      "type": "node",
      "entity1": "",
      "entity2": "",
      "chunk_id": False,
      "document_id": False,
    },
    {
      "level": 0,
      "type": "node",
      "entity1": "",
      "entity2": "",
      "chunk_id": False,
      "document_id": False,
    },
    {
      "level": 0,
      "type": "node",
      "entity1": "",
      "entity2": "",
      "chunk_id": False,
      "document_id": False,
    },
    {
      "level": 0,
      "type": "node",
      "entity1": "",
      "entity2": "",
      "chunk_id": False,
      "document_id": False,
    },
    {
      "level": 0,
      "type": "edge",
      "entity1": "apple",
      "entity2": "microsoft",
      "chunk_id": 1,
      "document_id": 1,
    },
    {
      "level": 0,
      "type": "property",
      "entity1": "sam altman",
      "entity2": "microsoft",
      "chunk_id": 2,
      "document_id": 2,
    },
    {
      "level": 0,
      "type": "property",
      "entity1": "amazon",
      "entity2": "",
      "chunk_id": 3,
      "document_id": 3,
    },
    {
      "level": 0,
      "type": "property",
      "entity1": "sam altman",
      "entity2": "",
      "chunk_id": 4,
      "document_id": 4,
    },
    {
      "level": 0,
      "type": "property",
      "entity1": "sam altman",
      "entity2": "",
      "chunk_id": 5,
      "document_id": 5,
    },
  ]

  # Insert documents into the vector database
  vectordb.insert_documents(
    documents=documents,
    metadata=metadatas,
    ids=[uuid4() for i in range(len(documents))],
    collection_name=collection_name,
  )

  test_query: str = "does sam eat meat?"

  r = search(query=test_query, vector_db=vectordb, model=llm)
  print(r)
