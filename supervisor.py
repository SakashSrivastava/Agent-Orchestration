from llm import call_llm_structured
from schemas import Plan, execution_order

SUPERVISOR_SYSTEM="""You are the supervisor of a team of specialist AI agents.
Break the user's task into the smallest reasonable number of subtasks

Your team:
- researcher: reads files from the workspace to gather information
- analyst: performs calculations and numeric analysis
- writer: writes final content to files in the workspace

Rules:
- Every subtask gets a unique integer id, starting at 1.
- If a subtask needs another subtask's output, list that id in depends on.
- Never assume a result you have not computed - if a value must be calculated, make it a subtask and have latter subtasks depend on it.
- Prefer 2-5 subtasks. Do not pad the plan with unnecessary steps."""

def make_plan(task: str) -> Plan:
    plan=call_llm_structured(prompt=task, schema=Plan, system=SUPERVISOR_SYSTEM)
    execution_order(plan)
    return plan
