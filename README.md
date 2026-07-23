# Agent Orchestration System

A multi-agent orchestration system built **from scratch**: no LangGraph, no CrewAI, no agent frameworks. A supervisor agent decomposes complex tasks into subtasks, specialist agents execute them using real tools, a reviewer agent validates their output, and a human approves sensitive actions before they run. Every step is traced with token usage, latency, and cost.

The goal: understand and own every layer that agent frameworks abstract away, including the planning loop, the tool-calling loop, state management, and observability.

## Architecture (target)

```
Your task
   │
   ▼
Supervisor agent ──── breaks the task into a dependency-ordered plan
   │
   ▼
Specialist agents ─── execute subtasks with tools (calculator, file I/O, search)
   │
   ▼
Reviewer agent ────── scores each output, rejects and retriggers bad work
   │
   ▼
Human approval ────── execution pauses on sensitive steps until approved
   │
   ▼
Final result ──────── with a full trace: every prompt, tool call, and cost
```

## Build status

| Stage | Status |
|---|---|
| LLM client wrapper (tokens, latency, cost tracking) | ✅ Done |
| Structured outputs (JSON mode + Pydantic validation + self-correcting retry) | ✅ Done |
| Tool registry + agentic tool-calling loop | ✅ Done |
| Supervisor agent (task decomposition into executable plans) | ✅ Done |
| Executor state machine + reviewer agent (evidence-based LLM-as-judge) | ✅ Done |
| Persistent task state (SQLite): crash recovery, pause/resume | ✅ Done |
| Long-term memory: lesson extraction, similarity recall into planning | ✅ Done |
| Human-in-the-loop approval queue (CLI + dashboard buttons) | ✅ Done |
| Call logging + Streamlit dashboard (tasks, costs, approvals, memory) | ✅ Done |
| End-to-end tests, Docker, demo | 🔨 In progress |

## Stack

- **Python 3.12**: core language, no agent frameworks
- **Groq API** (OpenAI-compatible): LLM inference; provider-agnostic client, swappable via one `base_url`
- **Pydantic**: typed, validated schemas for every data structure crossing an LLM boundary
- **SQLite** (stdlib): persistent task state, approval queue, long-term memory, call telemetry
- **Streamlit**: operations dashboard with task browser, cost analytics, approval buttons, memory viewer

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install openai pydantic python-dotenv streamlit
```

Create a `.env` file:

```
GROQ_API_KEY=gsk_...
```

Smoke test:

```bash
python test_llm.py          # basic call: text + tokens + cost + latency
python test_structured.py   # structured output: validated Pydantic object
```

Full pipeline and dashboard:

```bash
python test_executor.py     # plan -> specialists -> reviewer -> synthesized answer
python test_hitl.py         # runs until the writer needs approval, then pauses
python approve.py           # review the queue; approve/reject resumes the task
streamlit run dashboard.py  # task browser, cost analytics, approval buttons
```

## Design decisions

- **Never call the API directly from app logic.** Every call goes through one wrapper that captures tokens, latency, and cost, so observability is built in from the first line instead of retrofitted.
- **Rich objects at boundaries.** Functions return typed Pydantic models, not strings: extra fields can be ignored, but uncaptured fields can never be recovered.
- **Three layers of JSON defense.** Schema in the prompt → provider JSON mode → Pydantic validation with the error fed back to the model for self-correction.
- **Failures are information, not crashes.** The same pattern at every scale: invalid JSON is fed back for self-correction, tool errors return as strings the model can react to, malformed tool calls are retried, rejected work is redone with the reviewer's critique attached.
- **Subtasks are the unit of atomicity.** State is saved only at subtask boundaries: a subtask either fully happened or never happened, so resume never has to reconstruct half-finished LLM conversations.
- **Serializable state everywhere.** Plans and results are Pydantic/JSON, so execution can be frozen at any subtask boundary and resumed in a different process, which makes crash recovery and human approval the same feature.

## What broke and how I fixed it

- **The reviewer rejected correct work 5 times out of 6.** It was prompted to demand evidence but could only see the specialist's prose claims, so it kept asking for "code snippets" as proof. Fix: the tool-calling loop now records every executed tool call (name, args, result) in the executor's own code, and the reviewer receives that log as system-verified ground truth. Rejections went from 5/6 (all false) to 0/3 on the same workload.
- **Least privilege was silently broken.** The tool loop accepted a per-specialist tool subset but still passed the full registry to the API. Every specialist could use every tool, with no error and correct-looking output. Caught only by reading the code. This is the class of bug that motivates negative tests: assert the writer *cannot* calculate.
- **Groq's Llama intermittently emits malformed tool calls** (a 400 `tool_use_failed`, randomly). Fix: catch that specific error and retry within the step budget; any other 400 still crashes loudly. Recovery is targeted, never blanket.
- **Keyword-based memory recall missed "calculation" vs "calculate".** Jaccard similarity over exact tokens can't see morphology or synonyms. This is the concrete failure that motivates embeddings. Similarity lives behind one function, so swapping in embeddings touches one function.
- **Resuming an already-completed task re-ran synthesis and stored a duplicate memory.** Fix: terminal states (`done`, `failed`) refuse to resume. Guard entry points against invalid states.

## Known limitations (deliberate, documented)

- Memory recall is lexical (Jaccard), not semantic; embeddings are the designed upgrade path.
- Memories are not deduplicated on write; consolidation is planned.
- The reviewer is a single LLM judge; measuring its false-pass/false-reject rates is an evaluation problem (the subject of my next project).
- Approval triggers on specialist identity (writer = sensitive), which is blunt; per-tool or per-argument policies would be finer-grained.
