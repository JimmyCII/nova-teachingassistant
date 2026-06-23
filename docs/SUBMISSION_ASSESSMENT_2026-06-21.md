# Capstone Submission Assessment vs. Rubric — TeacherMind / Nova

**Date:** 2026-06-21 · **Deadline:** 2026-07-06 (15 days) · **Track:** Concierge Agents

## The rubric (as published by Kaggle/Google)

Judged on **innovation, solution design, communication, and effective application of course
concepts & agent technologies** — specifically: **problem definition · solution design ·
implementation quality · effective use of agent technologies · overall user value.**
**Required submission artifacts:** a **Kaggle Writeup**, a **public codebase**, a **video
demonstration**, and a **project link**. *(Confirm exact wording on the competition page.)*

## Scorecard

| Criterion | Rating | Evidence / gap |
|---|---|---|
| Problem definition | 🟢 Strong | Real 6th-grade AZ teacher; 3 siloed systems (Synergy/Canvas/School-Net); admin burden; standards-aligned. Concrete and documented. |
| Solution design | 🟢 Strong | Dual-MCP architecture (Curriculum + Comms) + content pipeline (generate → **pedagogy critic** → save) + **human-in-the-loop** approval loop. Well-specced. |
| Implementation quality | 🟡 Good | 22 tests green on `main`; two MCP servers on stdio; critic consumes MCP; **email approval test passing**; Dockerfile/deploy. Caveats below. |
| Effective use of agent tech / course concepts | 🟢 Strong | **≥3 cleanly met:** two MCP servers *actually consumed* + multi-agent critic pipeline + human-in-the-loop. Plus secure-deploy + SDD trail. |
| Overall user value | 🟢 Strong | Generates homework/quizzes/DOK in her style → her Drive → emails her to approve. Zero-friction; honors the North Star. |
| **Communication (writeup + video)** | 🔴 **Not started** | **The biggest gap.** No Kaggle writeup, no demo video, public-repo not confirmed. This is both a judged criterion *and* a hard submission requirement. |

## Course-concept claim (be precise with the judges)

You can confidently claim, with running evidence:
1. **MCP — two servers, genuinely consumed.** Curriculum (`standards://az-math-6` read by the
   critic) + Comms (`send_draft_for_approval` + `check_drive_approvals`). This is your strongest card.
2. **Multi-agent pipeline.** Generator → **Pedagogy/Standards Critic** → output. Real collaboration
   on one artifact (not routing). *Caveat:* this is function-orchestrated, **not** ADK `sub_agents`
   — so claim "multi-agent agentic pipeline," not "ADK multi-agent system," unless you build the
   orchestrator. Honest framing protects you.
3. **Human-in-the-loop.** Email-for-approval + Drive `03_Approved` signal + request-log status.
Supporting: **security** (token'd `/ws`), **spec-driven development** (the `docs/specs` trail).

## Risks to fix before submitting (ordered)

1. 🔴 **`key.txt` is committed to `main` and not gitignored.** The codebase must go **public** — a
   committed secret is a leak. Remove from history (filter-repo/BFG), rotate the value, gitignore it.
   Do this **before** the repo is made public. Non-negotiable.
2. 🔴 **Build the submission package.** Kaggle writeup, a short (2–4 min) demo video, a public repo,
   and a live project link. Communication is explicitly judged — right now it's the weakest criterion
   despite strong tech. **Most of your remaining time should go here.**
3. 🟠 **Deploy + phone-test for the "project link."** Deploy is scaffolded and token-fixed; it isn't
   confirmed live or mobile-tested. The judges want a working link.
4. 🟠 **Implementation caveats to tidy or disclose:** `group_activities` / `weekly_quiz` are untested;
   DOK output is Markdown (not the locked `.xlsx`); the critic's answer-key "check" is LLM
   self-review, not verified compute. Fine as v1 — just don't overclaim correctness in the writeup.

## Bottom line

**Substance: ~85% — the agent genuinely works and the concept story is strong.**
**Submission readiness: ~45% — the writeup/video/public-repo/live-link aren't done, and a secret is
in history.** The technical risk is largely behind you; the *packaging and a credential scrub* are
what stand between you and a competitive submission. Pivot the team from building to **shipping the
story**: scrub `key.txt`, deploy, record the demo, and write the Kaggle writeup.
