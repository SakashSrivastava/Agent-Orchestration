# Agent Orchestration System

A multi-agent orchestration system built **from scratch** — no LangGraph, no CrewAI, no agent frameworks. A supervisor agent decomposes complex tasks into subtasks, specialist agents execute them using real tools, a reviewer agent validates their output, and a human approves sensitive actions before they run. Every step is traced with token usage, latency, and cost.

The goal: understand and own every layer that agent frameworks abstract away — the planning loop, the tool-calling loop, state management, and observability.

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
| Tool registry + agentic tool-calling loop | 🔨 In progress |
| Supervisor agent (task decomposition into executable plans) | ⏳ Planned |
| Executor state machine + reviewer agent | ⏳ Planned |
| Working memory + long-term semantic memory | ⏳ Planned |
| Human-in-the-loop approval queue (FastAPI) | ⏳ Planned |
| Trace explorer + cost dashboard | ⏳ Planned |
| End-to-end tests, Docker, demo | ⏳ Planned |

## Stack

- **Python 3.12** — core language, no agent frameworks
- **Groq API** (OpenAI-compatible) — LLM inference; provider-agnostic client, swappable via one `base_url`
- **Pydantic** — typed, validated schemas for every data structure crossing an LLM boundary

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install openai pydantic python-dotenv
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

## Design decisions

- **Never call the API directly from app logic.** Every call goes through one wrapper that captures tokens, latency, and cost — observability is built in from the first line, not retrofitted.
- **Rich objects at boundaries.** Functions return typed Pydantic models, not strings: extra fields can be ignored, but uncaptured fields can never be recovered.
- **Three layers of JSON defense.** Schema in the prompt → provider JSON mode → Pydantic validation with the error fed back to the model for self-correction.
