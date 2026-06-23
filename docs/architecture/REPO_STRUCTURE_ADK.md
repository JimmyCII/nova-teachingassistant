# Repo Structure — ADK Alignment + De-"Superpowers" Rename

**Date:** 2026-06-21 · **Purpose:** make the repo *read* as an ADK multi-agent project to the judges,
and remove build-tool tells (Claude Code "superpowers", Codex). Complements `adk-migration.md`
(which covers the single-agent loop) by adding the **multi-agent layer** and the **layout**.

## Why this matters (rubric)

Judges score "effective use of agent technologies / course concepts." Two structural signals carry
most of that impression before they read a line of logic:
1. An **ADK agent package** with a clear `root_agent` and a `sub_agents/` folder = "this is a
   multi-agent ADK system." Its *absence* is why the orchestration doc's "Sub-Agent" claim feels thin.
2. **No build-tool tells.** `docs/superpowers/`, `CLAUDE.md`, `CODEX_BOOTSTRAP.md`,
   `docs/claude_settings.json`, and the `prompts/session-*` files announce "built with Claude Code,"
   not Antigravity/ADK. Harmless to the product, but they muddy the story you're being judged on.

## 1. The rename you asked for: `docs/superpowers/` → neutral

"Superpowers" is the Claude Code plugin name. Rename to plain, ADK-agnostic doc folders:

```
docs/superpowers/specs/  →  docs/specs/
docs/superpowers/plans/  →  docs/plans/
```

Commands (run in your shell — git is locked from my side):
```bash
git mv docs/superpowers/specs docs/specs
git mv docs/superpowers/plans docs/plans
rmdir docs/superpowers 2>/dev/null
# fix references:
grep -rl "superpowers" docs README.md AGENTS.md | xargs sed -i 's#docs/superpowers/specs#docs/specs#g; s#docs/superpowers/plans#docs/plans#g; s#superpowers:##g'
```
Then skim `README.md` / `AGENTS.md` for any remaining "superpowers:" skill references and reword.

## 2. The structural gap: there is no ADK agent layer yet

Today the "agent" is `agent/agent.py` (a hand-rolled function-calling loop) + `agent/voice_tools.py`
(a flat tool registry). There is **no `root_agent`, no `sub_agents/`**. That's the gap behind the
multi-agent concern. The target below adds it.

## 3. Target structure (annotated: KEEP / RENAME / ADD / MOVE)

> **Minimal-churn principle:** keep the package name `agent/` so you don't rewrite every
> `from agent.tools…` import 15 days out. Restructure *inside* it. (Renaming `agent/`→`nova/` is
> cleaner but touches every import — only if you have time.)

```
teacher-agent/                         # repo root
├── AGENTS.md                          # KEEP — ADK reads this natively (your strongest ADK signal already)
├── README.md                          # KEEP — update to describe the ADK root_agent + sub_agents
├── pyproject.toml                     # ADD — ADK/agents-cli projects are pyproject-based (keep requirements.txt too)
├── requirements.txt  Dockerfile  deploy.sh  .dockerignore   # KEEP
│
├── agent/                             # the ADK agent package (KEEP name; restructure inside)
│   ├── __init__.py                    # EDIT → `from .agent import root_agent`
│   ├── agent.py                       # EDIT → defines `root_agent = LlmAgent(name="Nova", sub_agents=[…], tools=[…])`
│   ├── sub_agents/                    # ADD ← THE multi-agent layer the judges look for
│   │   ├── __init__.py
│   │   ├── homework_agent.py          #   wraps spiral_homework generator
│   │   ├── quiz_agent.py              #   wraps weekly_quiz
│   │   ├── activity_agent.py          #   wraps group_activities (DOK)
│   │   └── critic_agent.py            #   pedagogy_critic as a reviewer/reflection agent
│   ├── tools/                         # KEEP — FunctionTools (grades, standards, canvas, comms, drive, mcp_client)
│   │   └── spiral_homework/           # KEEP — generator/renderer/drive as a tool module
│   ├── data/                          # KEEP — az_math_6_standards.json, az_dok_levels.json
│   └── voice_tools.py                 # KEEP (interim) → later: console calls root_agent directly (adk-migration §3)
│
├── mcp_servers/                       # KEEP — already ADK-idiomatic; your strongest concept card
│   ├── curriculum_server/             #   standards/pacing/drive
│   └── comms_server/                  #   approval email + drive-approved check
│
├── web/                               # KEEP — the voice console (UI surface)
├── eval/                              # ADD (optional, high-value) — ADK evalset(s); judges reward evals
├── tests/                             # KEEP — MOVE stray ./test_approval_loop.py in here
├── sample_data/                       # KEEP
│
└── docs/
    ├── specs/                         # RENAME ← docs/superpowers/specs
    ├── plans/                         # RENAME ← docs/superpowers/plans
    ├── architecture/                  # MOVE here: multi_agent_orchestration.md, adk-migration.md, this file
    ├── decision-log/                  # MOVE here ← agents/logs/  (agent-decision-log.md, routing-audit-log.md)
    └── (assessments, ideas, launch, runbook…)   # KEEP
```

## 4. Collisions / tells to resolve

| Item | Issue | Action |
|---|---|---|
| `agents/` (plural) **and** `agent/` (singular) | Judges see two near-identical dirs and get confused | MOVE `agents/logs` → `docs/decision-log/`; fold `agents/prompts/00-orchestrator.md` into the root agent's instruction (or `docs/architecture/`); delete `agents/` |
| `docs/superpowers/` | Claude Code plugin name | RENAME (§1) |
| `CLAUDE.md`, `CODEX_BOOTSTRAP.md`, `docs/claude_settings.json` | "built with Claude Code/Codex" | MOVE to `docs/build-journal/` (or delete). Keep `AGENTS.md` as the canonical agent config |
| `prompts/session-*-kickoff.md` | Claude Code session cadence | MOVE to `docs/build-journal/` — keep as honest process history, just out of the root |
| `key.txt` | committed secret | REMOVE from history + rotate (separate, urgent) |
| `docs/02_Generated/Quizzes/*.docx` | generated output in source control | gitignore `docs/02_Generated/`; keep one sample as a demo artifact if useful |
| `agent/agent.py` model `gemini-2.0-flash` | 2.0 had no free quota (you switched to 2.5) | sync to `gemini-2.5-flash` |

## 5. How the sub_agents map to ADK (makes "multi-agent" literally true)

```python
# agent/agent.py  (sketch — aligns with adk-migration.md §2)
from google.adk.agents import LlmAgent
from .sub_agents.homework_agent import homework_agent
from .sub_agents.quiz_agent import quiz_agent
from .sub_agents.activity_agent import activity_agent
from .sub_agents.critic_agent import critic_agent

root_agent = LlmAgent(
    name="Nova",
    model="gemini-2.5-flash",
    instruction=NOVA_PERSONA_PROMPT,
    sub_agents=[homework_agent, quiz_agent, activity_agent],  # delegation
    tools=[*CURRICULUM_MCP_TOOLS, *COMMS_MCP_TOOLS, get_recent_requests],
)
# critic_agent is invoked inside the content sub_agents as a reflection step.
```
Keep your **flat-tool fallback** (`NOVA_AGENT_MODE=flat`) so the current working path still runs if a
sub-agent fails — that's resilience the judges will appreciate, not a contradiction.

## 6. Suggested order (low-risk first)
1. **Rename `superpowers` → `specs`/`plans`** + move build-journal docs. Pure cosmetics, zero code risk.
2. **Delete the `agents/` vs `agent/` collision** (move logs/prompts into `docs/`).
3. **Add `agent/sub_agents/`** wrapping the existing generators (this is the real ADK win; spec in
   `docs/specs/2026-06-21-adk-orchestrator.md`).
4. **Add `pyproject.toml`** (and optionally an `eval/` set).
5. Sync the orchestration doc's language to this structure (no more "Sub-Agent" for a plain function).
