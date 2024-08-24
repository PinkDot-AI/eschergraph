# from __future__ import annotations
# import json
# import unittest
# from unittest.mock import MagicMock
# from unittest.mock import patch
# from eschergraph.agents.reranker import RerankerResult
# from eschergraph.exceptions import ExternalProviderException
# from eschergraph.graph.community import Finding
# from eschergraph.graph.search.global_search import extract_entities_from
# from eschergraph.graph.search.global_search import order_findings
# from eschergraph.graph.search.global_search import retrieve_key_findings
# from eschergraph.graph.search.global_search import retrieve_similar_findings
# class TestExtractEntitiesFrom(unittest.TestCase):
#   def setUp(self) -> None:
#     self.mock_llm = MagicMock()
#     self.mock_node_1 = MagicMock()
#     self.mock_node_1.report.findings = [
#       Finding("Summary 1", "Explanation 1"),
#       Finding("Summary 3", "Explanation 3"),
#     ]
#     self.mock_node_2 = MagicMock()
#     self.mock_node_2.report.findings = [
#       Finding("Summary 2", "Explanation 2"),
#       Finding("Summary 4", "Explanation 4"),
#     ]
#     self.mock_graph = MagicMock()
#     self.mock_graph.repository.get_max_level.return_value = 3
#     self.mock_embedder = MagicMock()
#     self.mock_embedder.get_embedding.return_value = [[0.1, 0.2, 0.3]]
#     self.mock_vecdb = MagicMock()
#     self.mock_vecdb.search.return_value = [{"id": "mock-node-id"}]
#     self.mock_vecdb.format_search_results.return_value = [{"id": "mock-node-id"}]
#     self.mock_reranker = MagicMock()
#     self.mock_reranker.rerank.return_value = [
#       RerankerResult(0, 0.8, "Text"),
#       RerankerResult(1, 0.7, "Text"),
#     ]
#     self.mock_node = MagicMock()
#     self.mock_node.report.findings = [
#       Finding("Mock Summary 1", "Mock Explanation 1"),
#       Finding("Mock Summary 2", "Mock Explanation 2"),
#     ]
#     self.mock_graph.repository.get_node_by_id.return_value = self.mock_node
#   def test_correct_entity_extraction(self) -> None:
#     entities = ["entity1", "entity2", "entity3"]
#     self.mock_llm.get_plain_response.return_value = json.dumps(entities)
#     result = extract_entities_from("Find entities in this query.", self.mock_llm)
#     self.assertEqual(result, entities)
#   def test_empty_response_raises_exception(self) -> None:
#     self.mock_llm.get_plain_response.return_value = None
#     with self.assertRaises(ExternalProviderException):
#       extract_entities_from("Find entities in this query.", self.mock_llm)
#   def test_invalid_json_raises_value_error(self) -> None:
#     self.mock_llm.get_plain_response.return_value = "not a json"
#     with self.assertRaises(ValueError):
#       extract_entities_from("Find entities in this query.", self.mock_llm)
#   def test_non_list_json_raises_value_error(self) -> None:
#     self.mock_llm.get_plain_response.return_value = json.dumps({"entity": "not a list"})
#     with self.assertRaises(ValueError):
#       extract_entities_from("Find entities in this query.", self.mock_llm)
#   def test_list_with_non_string_elements_raises_value_error(self) -> None:
#     self.mock_llm.get_plain_response.return_value = json.dumps([
#       "entity1",
#       42,
#       "entity3",
#     ])
#     with self.assertRaises(ValueError):
#       extract_entities_from("Find entities in this query.", self.mock_llm)
#   def test_empty_list_response(self) -> None:
#     self.mock_llm.get_plain_response.return_value = json.dumps([])
#     result = extract_entities_from("Find entities in this query.", self.mock_llm)
#     self.assertEqual(result, [])
#   def test_correct_ordering_of_findings(self) -> None:
#     findings_json = [
#       {"summary": "Finding 1", "explanation": "Explanation 1"},
#       {"summary": "Finding 2", "explanation": "Explanation 2"},
#     ]
#     mock_node = MagicMock()
#     mock_node.report.findings_to_json.return_value = json.dumps(findings_json)
#     self.mock_llm.get_formatted_response.return_value = json.dumps({
#       "findings": findings_json
#     })
#     result = order_findings(mock_node, self.mock_llm)
#     expected_findings = [
#       Finding("Finding 1", "Explanation 1"),
#       Finding("Finding 2", "Explanation 2"),
#     ]
#     self.assertEqual(result, expected_findings)
#   def test_empty_findings_response(self) -> None:
#     mock_node = MagicMock()
#     mock_node.report.findings_to_json.return_value = json.dumps([])
#     self.mock_llm.get_formatted_response.return_value = json.dumps({"findings": []})
#     result = order_findings(mock_node, self.mock_llm)
#     self.assertEqual(result, [])
#   def test_invalid_json_structure_raises_error(self) -> None:
#     mock_node = MagicMock()
#     mock_node.report.findings_to_json.return_value = json.dumps([])
#     self.mock_llm.get_formatted_response.return_value = json.dumps({"invalid_key": []})
#     with self.assertRaises(KeyError):
#       order_findings(mock_node, self.mock_llm)
#   def test_empty_response_raises_exception_in_order_findings(self) -> None:
#     mock_node = MagicMock()
#     self.mock_llm.get_formatted_response.return_value = None
#     with self.assertRaises(ExternalProviderException):
#       order_findings(mock_node, self.mock_llm)
#   def test_retrieve_top_n_sorted_findings(self) -> None:
#     mock_graph = MagicMock()
#     mock_graph.repository.get_max_level.return_value = 2
#     mock_graph.repository.get_all_at_level.return_value = [
#       self.mock_node_1,
#       self.mock_node_2,
#     ]
#     self.mock_node_1.report.findings = [Finding("Summary 1", "Explanation 1")]
#     self.mock_node_2.report.findings = [Finding("Summary 2", "Explanation 2")]
#     result = retrieve_key_findings(mock_graph, self.mock_llm, n=1, sorted=True)
#     expected_findings = [
#       Finding("Summary 1", "Explanation 1"),
#       Finding("Summary 2", "Explanation 2"),
#     ]
#     self.assertEqual(result, expected_findings)
#   def test_retrieve_top_n_unsorted_findings(self) -> None:
#     mock_graph = MagicMock()
#     mock_graph.repository.get_max_level.return_value = 2
#     mock_graph.repository.get_all_at_level.return_value = [
#       self.mock_node_1,
#       self.mock_node_2,
#     ]
#     self.mock_llm.max_threads = 2
#     self.mock_node_1.report.findings = None
#     self.mock_node_2.report.findings = None
#     self.mock_node_1.order_findings.return_value = [
#       Finding("Summary 1", "Explanation 1")
#     ]
#     self.mock_node_2.order_findings.return_value = [
#       Finding("Summary 2", "Explanation 2")
#     ]
#     with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
#       mock_executor.return_value.__enter__.return_value.map.return_value = [
#         self.mock_node_1.order_findings.return_value,
#         self.mock_node_2.order_findings.return_value,
#       ]
#       result = retrieve_key_findings(mock_graph, self.mock_llm, n=1, sorted=False)
#     expected_findings = [
#       Finding("Summary 1", "Explanation 1"),
#       Finding("Summary 2", "Explanation 2"),
#     ]
#     self.assertEqual(result, expected_findings)
#   def test_retrieve_key_findings_with_specified_level(self) -> None:
#     mock_graph = MagicMock()
#     mock_graph.repository.get_all_at_level.return_value = [self.mock_node_1]
#     self.mock_node_1.report.findings = [Finding("Summary 1", "Explanation 1")]
#     result = retrieve_key_findings(mock_graph, self.mock_llm, level=1, n=1, sorted=True)
#     expected_findings = [Finding("Summary 1", "Explanation 1")]
#     self.assertEqual(result, expected_findings)
#   def test_empty_findings_returned_when_no_findings_present(self) -> None:
#     mock_graph = MagicMock()
#     mock_graph.repository.get_max_level.return_value = 2
#     mock_graph.repository.get_all_at_level.return_value = [self.mock_node_1]
#     self.mock_node_1.report.findings = []
#     result = retrieve_key_findings(mock_graph, self.mock_llm, n=1, sorted=True)
#     self.assertEqual(result, [])
#   def test_retrieve_key_findings_with_unsorted_nodes_and_custom_n(self) -> None:
#     mock_graph = MagicMock()
#     mock_graph.repository.get_max_level.return_value = 2
#     mock_graph.repository.get_all_at_level.return_value = [
#       self.mock_node_1,
#       self.mock_node_2,
#     ]
#     self.mock_llm.max_threads = 2
#     self.mock_node_1.order_findings.return_value = [
#       Finding("Summary 1", "Explanation 1"),
#       Finding("Summary 3", "Explanation 3"),
#     ]
#     self.mock_node_2.order_findings.return_value = [
#       Finding("Summary 2", "Explanation 2"),
#       Finding("Summary 4", "Explanation 4"),
#     ]
#     with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
#       mock_executor.return_value.__enter__.return_value.map.return_value = [
#         self.mock_node_1.order_findings.return_value,
#         self.mock_node_2.order_findings.return_value,
#       ]
#       result = retrieve_key_findings(mock_graph, self.mock_llm, n=2, sorted=False)
#     expected_findings = [
#       Finding("Summary 1", "Explanation 1"),
#       Finding("Summary 3", "Explanation 3"),
#       Finding("Summary 2", "Explanation 2"),
#       Finding("Summary 4", "Explanation 4"),
#     ]
#     self.assertEqual(result, expected_findings)
#   def test_retrieve_similar_findings_success(self) -> None:
#     result = retrieve_similar_findings(
#       graph=self.mock_graph,
#       prompt="Test Prompt",
#       embedder=self.mock_embedder,
#       vecdb=self.mock_vecdb,
#       collection_name="test_collection",
#       reranker=self.mock_reranker,
#       levels_to_search=3,
#       findings_to_return=2,
#       top_vec_results=1,
#       top_node_findings=2,
#     )
#     expected_findings = [
#       Finding("Mock Summary 1", "Mock Explanation 1"),
#       Finding("Mock Summary 2", "Mock Explanation 2"),
#     ]
#     self.assertEqual(result, expected_findings)
#   def test_retrieve_similar_findings_no_nodes_found(self) -> None:
#     self.mock_vecdb.format_search_results.return_value = []
#     result = retrieve_similar_findings(
#       graph=self.mock_graph,
#       prompt="Test Prompt",
#       embedder=self.mock_embedder,
#       vecdb=self.mock_vecdb,
#       collection_name="test_collection",
#       reranker=self.mock_reranker,
#       levels_to_search=3,
#       findings_to_return=2,
#       top_vec_results=1,
#       top_node_findings=2,
#     )
#     self.assertEqual(result, [])
#   def test_retrieve_similar_findings_no_findings_in_node(self) -> None:
#     self.mock_node.report.findings = []
#     result = retrieve_similar_findings(
#       graph=self.mock_graph,
#       prompt="Test Prompt",
#       embedder=self.mock_embedder,
#       vecdb=self.mock_vecdb,
#       collection_name="test_collection",
#       reranker=self.mock_reranker,
#       levels_to_search=3,
#       findings_to_return=2,
#       top_vec_results=1,
#       top_node_findings=2,
#     )
#     self.assertEqual(result, [])
from __future__ import annotations
