# executor.py — deterministic machinery: walks the plan, dispatches specialists
from llm import call_llm
from reviewer import review_output
from schemas import Plan, Subtask, execution_order
from specialists import SPECIALISTS, schemas_for
from state import (create_approval, create_task, get_approval_status, load_task,
                   save_plan, save_result, set_status)
from supervisor import make_plan
from tool_agent import AgentResult, run_with_tools

MAX_ATTEMPTS = 2
SENSITIVE_SPECIALISTS = {"writer"}


def run_subtask(subtask: Subtask, results: dict[int, str], feedback: str = "") -> AgentResult:
    spec = SPECIALISTS[subtask.specialist]

    context = ""
    if subtask.depends_on:
        parts = [f"Result of subtask {d}:\n{results[d]}" for d in subtask.depends_on]
        context = "Context from completed subtasks:\n" + "\n\n".join(parts) + "\n\n"

    prompt = f"{context}Your subtask: {subtask.description}"
    if feedback:
        prompt += ("\n\nYour previous attempt was rejected by the reviewer. "
                   f"Reviewer feedback: {feedback}\nRedo the subtask and fix this.")
    return run_with_tools(prompt, system=spec["system"], tools=schemas_for(spec["tools"]))


def run_subtask_reviewed(subtask: Subtask, results: dict[int, str]) -> str:
    feedback = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result = run_subtask(subtask, results, feedback)
        review = review_output(subtask, result.text, result.tool_log)
        print(f"    review: {review.verdict} ({review.score}/5) {review.feedback[:90]}")
        if review.verdict == "approve":
            return result.text
        feedback = review.feedback
    print(f"    WARNING: subtask {subtask.id} still rejected after {MAX_ATTEMPTS} attempts")
    return result.text


def run_task(task: str, stop_after: int | None = None) -> str | None:
    task_id = create_task(task)
    print(f"TASK {task_id}")
    plan = make_plan(task)
    save_plan(task_id, plan)
    return _execute(task_id, task, plan, {}, stop_after)


def resume_task(task_id: str) -> str | None:
    task, status, plan, results = load_task(task_id)
    if status == "done":
        print(f"Task {task_id} is already complete - nothing to resume.")
        return None
    if status == "failed":
        print(f"Task {task_id} was rejected/failed - refusing to resume.")
        return None
    print(f"RESUMING {task_id} (was {status}, {len(results)} subtasks already done)")
    return _execute(task_id, task, plan, results)


def _execute(task_id: str, task: str, plan: Plan, results: dict[int, str],
             stop_after: int | None = None) -> str | None:
    for s in plan.subtasks:
        mark = "done" if s.id in results else "todo"
        print(f"  [{s.id}] ({mark}) {s.specialist}: {s.description}")

    for wave in execution_order(plan):
        for sid in wave:
            if sid in results:
                continue
            subtask = next(s for s in plan.subtasks if s.id == sid)

            if subtask.specialist in SENSITIVE_SPECIALISTS:
                approval = get_approval_status(task_id, sid)
                if approval is None:
                    create_approval(task_id, sid, subtask.description)
                    set_status(task_id, "paused")
                    print(f"\n    APPROVAL REQUIRED for subtask [{sid}] "
                          f"({subtask.specialist}): {subtask.description}")
                    print("    Run 'python approve.py' to review pending approvals.")
                    return None
                if approval == "rejected":
                    set_status(task_id, "failed")
                    print(f"    Subtask [{sid}] rejected by human reviewer - task marked failed.")
                    return None

            print(f"\n--- subtask [{sid}] -> {subtask.specialist} ---")
            results[sid] = run_subtask_reviewed(subtask, results)
            save_result(task_id, sid, results[sid])
            print(f"    done: {results[sid][:100]}")
            if stop_after == sid:
                set_status(task_id, "paused")
                print(f"    PAUSED after subtask {sid} - resume with resume_task('{task_id}')")
                return None

    summary = "\n".join(f"Subtask {i}: {r}" for i, r in results.items())
    final = call_llm(
        prompt=f"Original task: {task}\n\nCompleted subtask results:\n{summary}\n\n"
               "Write a brief final answer for the user.",
        system="You report completed work faithfully. Never invent results.",
    )
    set_status(task_id, "done")
    from memory import remember
    remember(task_id, task, summary)
    return final.text