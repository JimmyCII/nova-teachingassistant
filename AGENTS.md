# AGENTS.md — Working Agreement for AI Agents in This Repo

This is the **canonical** instruction file for any AI coding agent (Claude Code, Codex, etc.)
working in TeacherMind. `CLAUDE.md` and `CODEX_BOOTSTRAP.md` point here.

## What this project is
**TeacherMind** — an AI concierge agent (Gemini + Google ADK, Cloud Run) that reduces a 6th-grade
Arizona math teacher's admin burden. Canonical spec: `CAPSTONE_SPEC.md`. Scope/non-goals/acceptance:
`docs/requirements.md`. The agent persona is **Nova** (built in teacher Karrie's spirit — not a
clone). Kaggle Concierge-Agents capstone, due **2026-07-06**.

## Follow the playbook
Operate per `C:\Users\jimco\Dev\Project-Playbook\PROJECT-PLAYBOOK.md`. Key rules:
- **Plan before code.** Lock the data model / core logic before any UI. No app code until
  requirements + data model are settled.
- **Branch discipline.** `git init` + initial commit exists. Do all work on a **feature branch per
  increment** (`feat/v1-increment-N`). **Never build or commit on `main` without explicit consent.**
  Keep `main` releasable.
- **Checkpoint loop:** branch → build → verify (tests + type-check + lint) → fix inline → commit
  (`feat(scope):` / `fix(scope):` / `docs(scope):`) → merge after acceptance → one-line report.
- **Dependencies:** permissive licenses only (MIT/BSD/Apache-2.0); none new without a yes; record in
  `DEPENDENCIES.md`.
- **Destructive ops:** preview first; never `rm -rf`, `git push -f`, or `git reset --hard` without
  approval.

## ⚠ PII / FERPA — non-negotiable
This project derives from a real teacher's private files. **Never commit student PII.** The Karrie
research under `docs/karrie_profile/`, `docs/karrie_profile.md`, `docs/karrie_exploration_prompt.md`,
and any `*_raw.csv` are **gitignored / local-only** because they reference real student-name
filenames and IEP/SPED/SEI paths. Do not un-ignore or commit them until fully PII-scrubbed
(student names → `[STUDENT]`, IEP/SPED/SEI references removed). When in doubt, treat any individual
student data as untouchable: no names, IDs, grades, attendance, IEP/medical.

## Multi-agent / model routing (cost tiers)
Stay model-agnostic; route by capability tier (Project-Playbook §4): **Low** (Haiku-class) for
volume/scaffolding, **Medium** (Sonnet-class) for normal feature work, **High** (Opus-class) only
for architecture/security/high-impact + final pre-commit review. Default to the lowest sufficient
tier; record decisions in `agents/logs/routing-audit-log.md`.

## Where things live
- `agents/prompts/` — multi-agent role prompts · `agents/logs/` — routing + decision logs
- `prompts/` — session/build prompts (start with `prompts/session-1-kickoff.md`)
- `docs/` — requirements + (local-only) persona research · `agent/` — ADK agent code (no `src/`) ·
  `tests/` — tests
