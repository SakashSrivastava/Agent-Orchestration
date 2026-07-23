# memory.py — long-term lessons, extracted after tasks and recalled for planning
import sqlite3
import time
from pydantic import BaseModel
from llm import call_llm_structured

DB_PATH = "orchestrator.db"

STOPWORDS = {"the", "a", "an", "and", "or", "to", "of", "in", "is", "it",
             "for", "with", "on", "was", "were", "be", "this", "that", "from"}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        content TEXT NOT NULL,
        created_at REAL)""")
    return conn


def _keywords(text: str) -> set[str]:
    words = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def score_similarity(a: str, b: str) -> float:
    ka, kb = _keywords(a), _keywords(b)
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


class MemoryNote(BaseModel):
    lesson: str


def remember(task_id: str, task: str, summary: str) -> None:
    note = call_llm_structured(
        prompt=f"Task: {task}\n\nHow it went:\n{summary}\n\n"
               "Distill ONE reusable lesson for planning similar future tasks.",
        schema=MemoryNote,
        system="You extract short, general, reusable lessons - not restatements "
               "of what happened. Max 2 sentences.",
    )
    with _conn() as c:
        c.execute("INSERT INTO memories (task_id, content, created_at) VALUES (?,?,?)",
                  (task_id, f"[{task[:60]}] {note.lesson}", time.time()))


def recall(query: str, k: int = 3, min_score: float = 0.1) -> list[str]:
    with _conn() as c:
        rows = c.execute("SELECT content FROM memories").fetchall()
    scored = [(score_similarity(query, content), content) for (content,) in rows]
    scored = [(s, content) for s, content in scored if s >= min_score]
    scored.sort(reverse=True)
    return [content for _, content in scored[:k]]
