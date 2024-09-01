from __future__ import annotations

import json
import threading
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from typing import TypedDict

import nltk
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from eschergraph.agents.embedding import Embedding
from eschergraph.agents.embedding import get_embedding_model
from eschergraph.builder.build_log import BuildLog
from eschergraph.graph import Graph


class LogAnalysisResult(TypedDict):
  """This is a typed dict used in the evaluate information consistency in the graph."""

  chunk_num: int
  document_id: str
  similarity_mean_difference: float
  std_mean_difference: float
  possible_hallucinations: dict[str, int | float]
  possible_loss_of_information_sentences: list[dict[str, Any]]


def evaluate_information_consistency(graph: Graph) -> dict[str, float]:
  """Evaluate information consistency across the graph using parallel processing.

  Args:
    graph: The Graph object to evaluate.

  Returns:
    A dictionary containing statistical results of the evaluation.
  """
  data: list[LogAnalysisResult] = []
  lock = threading.Lock()

  def process_log(log) -> None:
    result = _handle_log(log, graph)
    with lock:
      data.append(result)

  with ThreadPoolExecutor() as executor:
    futures = [
      executor.submit(process_log, log) for log in graph.pre_persist_building_logs
    ]
    for future in as_completed(futures):
      future.result()
  output_path = f"eschergraph_storage/{graph.name}-graph_build_evaluation"
  with open(output_path, "w") as outfile:
    json.dump(data, outfile, indent=4)

  return _calculate_statistics(data)


def _calculate_statistics(data: list[LogAnalysisResult]) -> dict[str, float]:
  """Calculate statistics on similarity and standard deviation differences.

  Args:
    data: A list of LogAnalysisResult objects.

  Returns:
    A dictionary containing calculated statistics.
  """
  similarity_differences = [log["similarity_mean_difference"] for log in data]
  std_differences = [log["std_mean_difference"] for log in data]

  avg_similarity: float = float(round(np.mean(similarity_differences), 3))
  avg_std: float = float(round(np.mean(std_differences), 3))

  return {
    "Average of mean similarity differences ": avg_similarity,
    "Average of mean std difference": avg_std,
  }


def _handle_log(log: BuildLog, graph: Graph) -> LogAnalysisResult:
  """Process a single build log and analyze its content.

  Args:
      log: The BuildLog object to analyze.
      graph: The Graph object associated with the log.

  Returns:
      A LogAnalysisResult object containing the analysis results.
  """
  chunk_extractions: list[str] = []
  if log.edges:
    for edge in log.edges:
      chunk_extractions.append(edge["relationship"])
  if log.properties:
    for prop in log.properties:
      for p in prop:
        chunk_extractions.append(p)

  sentences_chunk: list[str] = nltk.tokenize.sent_tokenize(log.chunk_text.strip())
  embedding_model: Embedding = get_embedding_model()
  information_loss_sentences, hallucinated_sentences = _detector(
    graph, sentences_chunk, chunk_extractions
  )
  sim_mean_difference, similarity_std = _compare_sentence_and_extraction(
    embedding_model
  )

  return {
    "chunk_num": log.metadata.chunk_id,
    "document_id": log.metadata.document_id,
    "similarity_mean_difference": round(sim_mean_difference, 3),
    "std_mean_difference": round(similarity_std, 3),
    "possible_hallucinations": hallucinated_sentences,
    "possible_loss_of_information_sentences": information_loss_sentences,
  }


def _detector(
  graph: Graph, sentences_chunk: list[str], chunk_extractions: list[str]
) -> tuple[list[dict[str, Any]], dict[str, int | float]]:
  """Detect information loss and hallucinations in the given sentences and extractions.

  Args:
      graph: The Graph object to use for reranking.
      sentences_chunk: A list of sentences to analyze.
      chunk_extractions: A list of extracted information chunks.

  Returns:
      A tuple containing a list of information loss sentences and a dictionary of hallucinated sentences.
  """
  extraction_scores: dict[str, int | float] = dict.fromkeys(
    range(len(chunk_extractions)), 0
  )
  info_loss_sentences: list[dict[str, Any]] = []

  for sen in sentences_chunk:
    if sen.split() == "":
      continue

    ranked_extractions = graph.reranker.rerank(
      query=sen, text_list=chunk_extractions, top_n=len(chunk_extractions)
    )
    scores = [i["relevance_score"] for i in ranked_extractions]

    if not _detect_information_loss(scores):
      info_loss_sentences.append({
        "information_loss_sentence": sen,
        "top 3 json scores": [round(i, 3) for i in scores[:3]],
        "top 3 json text": [
          r["document"]["text"] for num, r in enumerate(ranked_extractions) if num < 3
        ],
      })

    for extract in ranked_extractions:
      extraction_scores[extract["index"]] = max(
        extraction_scores[extract["index"]], extract["relevance_score"]
      )

  hallucinated_sentences = _filter_hallucinations(
    chunk_extractions, extraction_scores, threshold=0.4
  )
  return info_loss_sentences, hallucinated_sentences


def _detect_information_loss(scores: list[float]) -> bool:
  """Detect if there is information loss based on relevance scores.

  Args:
    scores: A list of relevance scores.

  Returns:
    True if there is no information loss, False otherwise.
  """
  return sum(1 for score in scores if score > 0.5) >= 1


def _filter_hallucinations(
  chunk_extractions: list[str],
  extraction_scores: dict[str, int | float],
  threshold: int = 0.4,
) -> list[dict]:
  """Filter out potential hallucinations based on extraction scores.

  Args:
    chunk_extractions: A list of extracted information chunks.
    extraction_scores: A dictionary of extraction scores.
    threshold: The threshold score for considering an extraction as a hallucination.

  Returns:
    A list of dictionaries containing potential hallucinations.
  """
  return [
    {
      "extracted text": chunk_extractions[i],
      "relevance score": round(score, 3),
      "threshold": threshold,
    }
    for i, score in extraction_scores.items()
    if score < threshold
  ]


def _compare_sentence_and_extraction(
  embedding: Embedding, sentences: list[str], json_list: list[str]
) -> tuple[float, float]:
  """Compare sentences and extractions using embeddings and cosine similarity.

  Args:
    embedding: The Embedding object to use for generating embeddings.
    sentences: A list of sentences to compare.
    json_list: A list of JSON extractions to compare.

  Returns:
    A tuple containing the similarity mean difference and standard deviation difference.
  """
  sentences_embeddings = embedding.get_embedding(text_list=sentences)
  sentence_embeddings_matrix = np.array(sentences_embeddings)
  sentence_centroid = np.mean(sentence_embeddings_matrix, axis=0)
  sentences_similarities = cosine_similarity(
    sentence_embeddings_matrix, sentence_centroid.reshape(1, -1)
  ).flatten()

  json_embeddings = embedding.get_embedding(text_list=json_list)
  json_embeddings_matrix = np.array(json_embeddings)
  json_similarities = cosine_similarity(
    json_embeddings_matrix, sentence_centroid.reshape(1, -1)
  ).flatten()

  sentence_sim_std = np.std(sentences_similarities)
  json_sim_std = np.std(json_similarities)

  sentence_sim_mean = np.mean(sentences_similarities)
  json_sim_mean = np.mean(json_similarities)

  similarity_mean_difference = np.abs(sentence_sim_mean - json_sim_mean)
  std_difference = np.abs(sentence_sim_std - json_sim_std)

  return similarity_mean_difference, std_difference
