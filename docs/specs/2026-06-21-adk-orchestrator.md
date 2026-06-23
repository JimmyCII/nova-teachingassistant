# Spec — Nova as ADK Multi-Agent Orchestrator (v1)

**Date:** 2026-06-21 · **Status:** DRAFT for review · **Author:** Jim + Nova
**Part of:** the architecture push. Demonstrates the **multi-agent ADK** course concept and turns
the scattered tools into one Nova the teacher talks to.
**Depends on:** DOK builder, Pacing+Progress, Drive/Curriculum MCP (the specialists' tools).
**Formalizes:** the existing `agents/prompts/00-orchestrator.md` scaffold.
**Roster refined by:** `2026-06-21-multi-agent-content-pipeline.md` — the specialists below evolve
from "Homework/DOK/Progress routing" into a **generate → critique → enrich** pipeline plus a
performance loop. Read that doc for the agent roster; this spec governs the ADK wiring + fallback.

## Goal
Restructure Nova as a **root orchestrator agent over a small set of specialist sub-agents**, built
with Google **ADK**, so a single conversational Nova can route the teacher's request to the right
specialist (homework, DOK, progress) — each with its own focused prompt and tools. This is the
multi-agent system the capstone is judged on, and it unifies today's separate CLI tools + voice
console behind one agent. Ship a runnable v1 by **2026-07-06**.

## Decisions (proposed → confirm)
- **Pattern: coordinator + specialists, with a flat-tool fallback** (CONFIRMED 2026-06-21).
  **Primary:** root `LlmAgent` ("Nova") with the three specialists as **`sub_agents`** (autonomous
  routing). Curriculum lookup is a **tool**, not an agent (deterministic retrieval).
  **Fallback (required):** a **single-agent mode** where the specialists' underlying tools
  (`generate_week_spec`, `generate_dok_activity`, the MCP tools, the analytics tools) are registered
  **directly on the Nova root agent** as flat `FunctionTool`s — so if `sub_agents` are unavailable,
  mis-routing, or a runtime/SDK version doesn't support the topology, Nova still does every job from
  one agent. A `NOVA_AGENT_MODE=multi|flat` env switch (default `multi`, auto-degrade to `flat` on
  sub-agent init failure) selects between them; both build from the **same tool registry** so there's
  no duplicate logic.
- **Keep it to 3 specialists.** Homework, DOK, Progress/Insights. No agents-for-agents'-sake.
- **Nova carries the persona.** The root agent's instruction = Nova's voice (warm, "I can…",
  Socratic, "Oops!") — finally wiring the persona that `session-1/2` flagged as the open gap.
- **All data via the Drive/Curriculum MCP** (and the existing `agent/tools/` analytics). Specialists
  don't each re-implement Drive.
- **One shared surface.** The same orchestrator backs both the CLI (`run.py`) and the voice console
  (`web/`), so "Nova can talk AND do things" is true on every surface (incl. the future phone deploy).

## Agent topology
```
Nova (root LlmAgent — persona, clarifies, routes)
├── Homework specialist   → tools: generate_week_spec, render, MCP.save_draft, MCP.get_current_pacing
├── DOK specialist        → tools: generate_dok_activity, generate_dok_ladder, render, MCP.save_draft
└── Progress specialist   → tools: MCP.get_progress, analyze_grade_trends, get_at_risk_students,
                                   get_class_standard_gaps, draft_class_digest
shared tools on root: MCP.get_current_pacing/get_next_pacing, get_standard_info, draft_parent_communication
```

## Architecture
- `agent/orchestrator.py` — builds the root ADK agent + the three sub-agents, each with its
  instruction (persona-aware) and tool list. Wraps existing Python tools as ADK
  `FunctionTool`s and the MCP server as an MCP toolset.
- Specialist instructions live in `agents/prompts/` (extend the existing `00-orchestrator.md`):
  `homework-specialist.md`, `dok-specialist.md`, `progress-specialist.md`.
- The existing hand-rolled loop in `agent/agent.py` becomes a thin **fallback/CLI** or is replaced
  by the ADK `Runner`; the 12 tools it defines are reused as ADK tools (don't rewrite them).
- Routing/decision logging continues in `agents/logs/` (already present).

## Data flow
Teacher (CLI or voice) → **Nova root** clarifies intent (one Socratic question if needed) → routes
to a specialist → specialist calls its tools (generators + MCP) → draft lands in Drive / report
returns → Nova summarizes in persona, human-in-the-loop on every outward step.

## Error handling
- Specialist tool error → Nova surfaces it warmly and offers the next step (never a raw stack trace).
- Ambiguous request → root asks **one** clarifying question, then routes (no over-generation).
- MCP/Drive down → specialists use local fallback (per their specs); Nova tells the teacher where
  the file is.
- Routing miss → if no specialist fits, Nova answers directly or asks what she'd like to tackle.

## Testing
- Routing tests: canned user turns → assert the correct specialist/tool is selected (mock the LLM
  routing decision where possible; otherwise a small live eval set).
- Specialist tool-wiring tests: each sub-agent can invoke its tools (mocked generators/MCP).
- Persona smoke test: greeting + a homework request returns in Nova's voice and produces a draft.
- Reuse existing tool unit tests unchanged.

## Acceptance criteria (v1 "done")
- [ ] One ADK root agent ("Nova") routes to Homework, DOK, and Progress sub-agents.
- [ ] "Build this week's spiral homework" → Homework specialist uses the pacing row → draft in Drive.
- [ ] "Make a DOK 1–3 set for 6.RP.A.3" → DOK specialist → activity + key in Drive.
- [ ] "How's Period 2 doing?" → Progress specialist → standard-by-standard report (anonymous data).
- [ ] Nova responds in persona throughout (closes the persona-wiring gap).
- [ ] Same orchestrator runs from the CLI and is callable by the voice console.
- [ ] **Flat-tool fallback works:** with `NOVA_AGENT_MODE=flat`, Nova performs all three jobs from a
      single agent with the tools registered directly; auto-degrades if sub-agent init fails.
- [ ] Routing + wiring tests pass (both `multi` and `flat` modes); no PII; human-in-the-loop on all
      outward actions.

## Out of scope (v1) / later
- ❌ A2A across machines / external agents (single-process multi-agent for v1).
- ❌ Autonomous actions (sending comms, writing grades) — always draft + review.
- ❌ A Curriculum/Pacing *agent* (it's a tool); a Canvas specialist (after the Canvas MCP exists).
- ❌ Cloud deploy of the orchestrator (tracked separately in the deployment plan).
