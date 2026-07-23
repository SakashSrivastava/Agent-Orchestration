# reviewer.py — independent quality gate for specialist outputs
from llm import call_llm_structured
from schemas import Review, Subtask

REVIEWER_SYSTEM = """You are a strict quality reviewer for an AI agent team.
You are shown a subtask and the specialist's output. Judge only whether the
output actually accomplishes the subtask.

Reject if the output: invents data not present in its inputs, skips part of
the subtask, reports doing something without evidence it was done, or is
vague where the subtask demanded specifics.

Approve only work you would stake your reputation on. When rejecting, give
one concrete, actionable instruction for the retry - not general advice.

The tool call list is ground truth - judge claims against it. Never ask for
code snippets or additional proof; the evidence you have is complete."""


def review_output(subtask: Subtask, result_text: str, tool_log: list[str]) -> Review:
    evidence = "\n".join(tool_log) if tool_log else "(no tools were invoked)"
    prompt = (f"Subtask: {subtask.description}\n"
              f"Specialist: {subtask.specialist}\n\n"
              f"Tool calls actually executed (verified by the system, not claimed "
              f"by the specialist):\n{evidence}\n\n"
              f"Specialist's report:\n{result_text}\n\n"
              "Review this output.")
    return call_llm_structured(prompt=prompt, schema=Review, system=REVIEWER_SYSTEM)