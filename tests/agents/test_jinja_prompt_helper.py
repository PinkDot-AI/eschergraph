from __future__ import annotations

from pinkgraph.agents.jinja_helper import process_template

string_template: str = """Add the properties as described in the execution plan to each of the entities exactly as listed.

The execution plan:
{execution_plan}

Add the listed properties to each node with a function call! Do not miss a single one!!
Lives may depend on it!!! Mistakes are extremely costly for me and my career!"""

execution_plan: str = "Do nothing this is a test!"

template_name: str = "property.jinja"


def test_templating_function() -> None:
  assert process_template(
    template_file=template_name, data={"execution_plan": execution_plan}
  ) == string_template.format(execution_plan=execution_plan)
