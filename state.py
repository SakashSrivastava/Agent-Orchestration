# state.py — every task's progress, persisted after every step
import json
import sqlite3
import time
import uuid
from schemas import Plan

DB_PATH = "orchestrator.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        task TEXT NOT NULL,
        status TEXT NOT NULL,
        plan_json TEXT,
        results_json TEXT NOT NULL DEFAULT '{}',
        created_at REAL,
        updated_at REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        subtask_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at REAL,
        resolved_at REAL)""")
    return conn


def create_task(task: str) -> str:
    task_id = uuid.uuid4().hex[:8]
    now = time.time()
    with _conn() as c:
        c.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?)",
                  (task_id, task, "planning", None, "{}", now, now))
    return task_id


def save_plan(task_id: str, plan: Plan) -> None:
    with _conn() as c:
        c.execute("UPDATE tasks SET plan_json=?, status='running', updated_at=? WHERE id=?",
                  (plan.model_dump_json(), time.time(), task_id))


def save_result(task_id: str, subtask_id: int, result: str) -> None:
    with _conn() as c:
        row = c.execute("SELECT results_json FROM tasks WHERE id=?", (task_id,)).fetchone()
        results = json.loads(row[0])
        results[str(subtask_id)] = result
        c.execute("UPDATE tasks SET results_json=?, updated_at=? WHERE id=?",
                  (json.dumps(results), time.time(), task_id))


def set_status(task_id: str, status: str) -> None:
    with _conn() as c:
        c.execute("UPDATE tasks SET status=?, updated_at=? WHERE id=?",
                  (status, time.time(), task_id))


def create_approval(task_id: str, subtask_id: int, description: str) -> None:
    with _conn() as c:
        c.execute("INSERT INTO approvals (task_id, subtask_id, description, status, created_at) "
                  "VALUES (?,?,?,?,?)",
                  (task_id, subtask_id, description, "pending", time.time()))


def get_approval_status(task_id: str, subtask_id: int) -> str | None:
    with _conn() as c:
        row = c.execute("SELECT status FROM approvals WHERE task_id=? AND subtask_id=? "
                        "ORDER BY id DESC LIMIT 1", (task_id, subtask_id)).fetchone()
    return row[0] if row else None


def list_pending_approvals() -> list[tuple]:
    with _conn() as c:
        return c.execute("SELECT id, task_id, subtask_id, description FROM approvals "
                         "WHERE status='pending'").fetchall()


def resolve_approval(approval_id: int, status: str) -> str:
    with _conn() as c:
        row = c.execute("SELECT task_id FROM approvals WHERE id=?", (approval_id,)).fetchone()
        if row is None:
            raise ValueError(f"No approval with id {approval_id}")
        c.execute("UPDATE approvals SET status=?, resolved_at=? WHERE id=?",
                  (status, time.time(), approval_id))
    return row[0]


def load_task(task_id: str) -> tuple[str, str, Plan, dict[int, str]]:
    with _conn() as c:
        row = c.execute("SELECT task, status, plan_json, results_json FROM tasks WHERE id=?",
                        (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"No task with id {task_id}")
    task, status, plan_json, results_json = row
    plan = Plan.model_validate_json(plan_json)
    results = {int(k): v for k, v in json.loads(results_json).items()}
    return task, status, plan, results
