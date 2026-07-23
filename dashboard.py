# dashboard.py — the visible face of the orchestrator: tasks, costs, approvals, memory
import json
import sqlite3
import time
import streamlit as st

from executor import resume_task
from schemas import Plan
from state import list_pending_approvals, resolve_approval

DB_PATH = "orchestrator.db"


def _ensure_tables() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS llm_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL, caller TEXT, model TEXT,
        input_tokens INTEGER, output_tokens INTEGER,
        cost_usd REAL, latency_s REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        content TEXT NOT NULL,
        created_at REAL)""")
    conn.commit()
    conn.close()


_ensure_tables()

st.set_page_config(page_title="Agent Orchestrator", layout="wide")
st.title("Agent orchestrator")


def q(sql: str, params: tuple = ()) -> list[tuple]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


tab_overview, tab_tasks, tab_approvals, tab_memory = st.tabs(
    ["Overview", "Tasks", "Approvals", "Memory"])


with tab_overview:
    calls = q("SELECT COUNT(*), COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), "
              "COALESCE(SUM(cost_usd),0), COALESCE(AVG(latency_s),0) FROM llm_calls")[0]
    n_tasks = q("SELECT COUNT(*) FROM tasks")[0][0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tasks run", n_tasks)
    c2.metric("LLM calls", calls[0])
    c3.metric("Tokens", f"{calls[1] + calls[2]:,}")
    c4.metric("Cost (if paid)", f"${calls[3]:.4f}")
    c5.metric("Avg latency", f"{calls[4]:.2f}s")

    st.subheader("Calls by caller")
    by_caller = q("SELECT caller, COUNT(*), SUM(cost_usd), AVG(latency_s) "
                  "FROM llm_calls GROUP BY caller ORDER BY 2 DESC")
    st.dataframe([{"caller": r[0], "calls": r[1], "cost_usd": round(r[2], 6),
                   "avg_latency_s": round(r[3], 2)} for r in by_caller],
                 use_container_width=True)


with tab_tasks:
    tasks = q("SELECT id, status, task, created_at FROM tasks ORDER BY created_at DESC")
    if not tasks:
        st.info("No tasks yet - run one with test_executor.py or test_hitl.py")
    else:
        options = {f"{t[0]}  [{t[1]}]  {t[2][:60]}": t[0] for t in tasks}
        choice = st.selectbox("Select a task", list(options.keys()))
        task_id = options[choice]

        row = q("SELECT task, status, plan_json, results_json, created_at "
                "FROM tasks WHERE id=?", (task_id,))[0]
        task, status, plan_json, results_json, created = row
        st.markdown(f"**Status:** `{status}` &nbsp;&nbsp; "
                    f"**Created:** {time.strftime('%Y-%m-%d %H:%M', time.localtime(created))}")
        st.markdown(f"**Request:** {task}")

        if plan_json:
            plan = Plan.model_validate_json(plan_json)
            results = json.loads(results_json)
            st.subheader("Plan and results")
            for s in plan.subtasks:
                done = str(s.id) in results
                icon = "✅" if done else "⬜"
                deps = f" (needs {s.depends_on})" if s.depends_on else ""
                with st.expander(f"{icon} [{s.id}] {s.specialist}: {s.description}{deps}",
                                 expanded=False):
                    if done:
                        st.text(results[str(s.id)])
                    else:
                        st.caption("Not executed yet.")


with tab_approvals:
    pending = list_pending_approvals()
    if not pending:
        st.success("No pending approvals.")
    else:
        for aid, t_id, sid, desc in pending:
            with st.container(border=True):
                st.markdown(f"**Task `{t_id}` - subtask {sid}**")
                st.markdown(desc)
                col_a, col_r = st.columns(2)
                if col_a.button("Approve and resume", key=f"a{aid}", type="primary"):
                    resolve_approval(aid, "approved")
                    with st.spinner(f"Resuming task {t_id}..."):
                        final = resume_task(t_id)
                    if final:
                        st.success(final)
                    st.rerun()
                if col_r.button("Reject", key=f"r{aid}"):
                    resolve_approval(aid, "rejected")
                    resume_task(t_id)
                    st.warning("Rejected - task marked failed.")
                    st.rerun()


with tab_memory:
    memories = q("SELECT content, created_at FROM memories ORDER BY created_at DESC")
    if not memories:
        st.info("No memories stored yet.")
    else:
        st.caption(f"{len(memories)} memories")
        for content, created in memories:
            st.markdown(f"- {content}  \n"
                        f"  *{time.strftime('%Y-%m-%d %H:%M', time.localtime(created))}*")
