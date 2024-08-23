from __future__ import annotations

import json

from eschergraph.graph.community import Finding
from eschergraph.graph.community import Report


def test_report_findings_to_json() -> None:
  example_json = [
    {
      "summary": "Explanations",
      "explanation": "Explaining complicated topics well is a skill",
    },
    {
      "summary": "Kangaroos are marsupials",
      "explanation": "They are from the Macropodidae family (macropods, meaning 'large foot')",
    },
  ]

  fd1 = Finding(
    explanation="Explaining complicated topics well is a skill", summary="Explanations"
  )
  fd2 = Finding(
    explanation="They are from the Macropodidae family (macropods, meaning 'large foot')",
    summary="Kangaroos are marsupials",
  )
  rp = Report(
    title="Some title", summary="Kangaroos and explanations", findings=[fd1, fd2]
  )

  assert rp.findings_to_json() == json.dumps(example_json, indent=4)
