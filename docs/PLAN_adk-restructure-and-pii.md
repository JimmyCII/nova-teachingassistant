# Implementation Plan — PII Scrub + ADK Restructure (for Antigravity)

**Date:** 2026-06-21 · **Implement in:** Google Antigravity IDE · **Deadline:** 2026-07-06
**Do the phases in order.** Phase A is a **gate** — finish it before the repo is made public.
Companion docs: `REPO_STRUCTURE_ADK.md` (target layout) · `adk-migration.md` (single-agent loop) ·
`specs/2026-06-21-adk-orchestrator.md` (multi-agent design).

---

## Phase A — PII / secret scrub (PRE-PUBLIC GATE)

> Audit (2026-06-21) found the repo mostly clean: `karrie_profile/` never committed; sample data
> synthetic; no real student data. **Two real items remain — both are in git *history*, so file
> edits alone don't remove them.**

- [ ] **A1 — Replace the family email with an env var / placeholder.** `redacted@example.com` appears
  in `prompts/session-3-kickoff.md` and `test_approval_loop.py`. Replace with `KARRIE_EMAIL`
  (already the pattern in `spiral_homework/__main__.py`) or `karrie@example.com` in docs/tests.
- [ ] **A2 — Move `test_approval_loop.py`** into `tests/` and make its recipient `os.getenv("KARRIE_EMAIL","karrie@example.com")` — no real address in code.
- [ ] **A3 — Decide on `docs/launch/`.** It names Karrie as your wife + says her photos were analyzed.
  Recommend **moving `docs/launch/` out of the submission repo** (it's LinkedIn marketing, not the
  agent). If you keep it, that's a conscious choice — note it.
- [ ] **A4 — gitignore generated output:** add `docs/02_Generated/` to `.gitignore`; `git rm --cached`
  the committed `.docx` quizzes (keep one as a demo artifact if useful). Spot-checked clean, but
  generated content shouldn't live in source.
- [ ] **A5 — History scrub (covers email + `key.txt` together).** File edits don't remove what's in
  history. Once, before going public:
  ```bash
  cp -r . ../teacher-agent-backup            # safety copy first
  pip install git-filter-repo
  git filter-repo --path key.txt --invert-paths
  git filter-repo --replace-text <(echo "redacted@example.com==>redacted@example.com")
  ```
  Then **rotate** any real secret value in `key.txt` (treat as compromised) and force-push.
- [ ] **A6 — Final sweep:** `git grep -niE "cox\.net|jfc_and_kac"` returns nothing; confirm
  `sample_data` names are fabricated (they look synthetic — just eyeball for accidental real matches).
- [ ] **Acceptance:** no real personal email or secret in working tree *or* history; generated output
  un-tracked; launch decision made.

---

## Phase B — De-"superpowers" rename + structure cleanup (low risk, cosmetics)

- [ ] **B1 — Rename the docs folders:**
  ```bash
  git mv docs/superpowers/specs docs/specs
  git mv docs/superpowers/plans docs/plans
  rmdir docs/superpowers
  ```
- [ ] **B2 — Fix references:**
  ```bash
  grep -rl "superpowers" . --include=*.md | xargs sed -i \
    's#docs/superpowers/specs#docs/specs#g; s#docs/superpowers/plans#docs/plans#g; s#superpowers:##g'
  ```
  Then reword any remaining "superpowers:brainstorming/writing-plans" mentions to neutral phrasing.
- [ ] **B3 — Kill the `agent/` vs `agents/` collision:** `git mv agents/logs docs/decision-log`;
  move `agents/prompts/00-orchestrator.md` → `docs/architecture/` (or fold into the root-agent
  instruction in Phase C); remove the empty `agents/` dir.
- [ ] **B4 — Quarantine build-tool tells:** `mkdir docs/build-journal`; move `CODEX_BOOTSTRAP.md`,
  `docs/claude_settings.json`, and `prompts/session-*-kickoff.md` there. Keep `AGENTS.md` at root
  (ADK reads it). `CLAUDE.md` → `docs/build-journal/` too (or delete).
- [ ] **B5 — Move stray docs:** `multi_agent_orchestration.md`, `adk-migration.md`, `REPO_STRUCTURE_ADK.md`,
  this plan → `docs/architecture/`.
- [ ] **Acceptance:** no `superpowers/`, no top-level `agents/`, no Claude/Codex files in the root;
  `git grep -ri superpowers` is clean; tests still pass.

---

## Phase C — Add the ADK agent layer (the real "multi-agent" win)

> Keep the package name `agent/` (avoids rewriting every `from agent.tools…` import). Restructure
> *inside* it. This is what turns the orchestration doc's "Sub-Agent" claim into something true.

- [ ] **C1 — Create `agent/sub_agents/`** with one thin `LlmAgent` per worker, each wrapping an
  existing generator as its tool (near-zero new logic):
  - `homework_agent.py` → tool: `generate_spiral_homework`
  - `quiz_agent.py` → tool: `generate_weekly_quiz`
  - `activity_agent.py` → tool: `generate_dok_activity`
  - `critic_agent.py` → `pedagogy_critic.review_and_revise` (the reflection reviewer)
- [ ] **C2 — Define `root_agent` in `agent/agent.py`** (replaces the hand-rolled loop per `adk-migration.md`):
  ```python
  from google.adk.agents import LlmAgent
  from .sub_agents.homework_agent import homework_agent
  from .sub_agents.quiz_agent import quiz_agent
  from .sub_agents.activity_agent import activity_agent

  root_agent = LlmAgent(
      name="Nova", model="gemini-2.5-flash",
      instruction=NOVA_PERSONA_PROMPT,
      sub_agents=[homework_agent, quiz_agent, activity_agent],
      tools=[*CURRICULUM_MCP_TOOLS, *COMMS_MCP_TOOLS, get_recent_requests],
  )
  ```
- [ ] **C3 — Keep the `flat` fallback:** `NOVA_AGENT_MODE=multi|flat` (default `multi`, auto-degrade
  to `flat` on sub-agent init failure) off the same tool registry — resilience, not duplication.
- [ ] **C4 — Point the voice console at `root_agent`** (`web/server.py`) so Nova uses tools natively
  over the live socket (`adk-migration.md` §3), retiring the manual `voice_tools` dispatch.
- [ ] **C5 — Tests:** one routing test (request → correct sub-agent) in `multi`; one `flat`-mode test;
  reuse existing tool tests.
- [ ] **C6 — Sync the prose:** update `docs/architecture/multi_agent_orchestration.md` to say
  `LlmAgent` + `sub_agents` (stop calling a plain function a "Sub-Agent").
- [ ] **Acceptance:** `root_agent` exists with real `sub_agents`; "build this week's quiz",
  "make a DOK activity", "how's Period 2?" route correctly; `flat` fallback works; tests green.

---

## Phase D — ADK packaging (optional but high-value)

- [ ] **D1 — Add `pyproject.toml`** (ADK/agents-cli projects are pyproject-based; keep `requirements.txt`).
- [ ] **D2 — Add an `eval/` set** — a small ADK evalset (a few prompts + expected tool calls). Judges
  reward evaluation discipline; it's a course concept (Day 4).
- [ ] **D3 — Update `README.md`** to describe the ADK architecture (root_agent, sub_agents, two MCP
  servers) so the structure and the writeup agree.

---

## Suggested Antigravity execution order
A (gate) → B (cosmetics) → C (the ADK win) → D (packaging). A and B are low-risk and make the repo
safe + clean to open publicly; C is the substantive change; D polishes the ADK story for the judges.
