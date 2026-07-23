# approve.py — the human side of human-in-the-loop
import sys
from executor import resume_task
from state import list_pending_approvals, resolve_approval


def main() -> None:
    if len(sys.argv) == 1:
        pending = list_pending_approvals()
        if not pending:
            print("No pending approvals.")
            return
        print("Pending approvals:")
        for aid, task_id, sid, desc in pending:
            print(f"  [{aid}] task {task_id}, subtask {sid}: {desc}")
        print("\nUse: python approve.py approve <id>   or   python approve.py reject <id>")
        return

    if len(sys.argv) != 3 or sys.argv[1] not in ("approve", "reject"):
        print("Usage: python approve.py [approve|reject] <id>")
        return

    action, aid = sys.argv[1], int(sys.argv[2])
    status = "approved" if action == "approve" else "rejected"
    task_id = resolve_approval(aid, status)
    print(f"Approval {aid} -> {status}. Resuming task {task_id}...\n")
    final = resume_task(task_id)
    if final:
        print("\nFINAL:", final)


if __name__ == "__main__":
    main()
