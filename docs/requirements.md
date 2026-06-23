# Requirements — TeacherMind

> Companion to the canonical `CAPSTONE_SPEC.md`. This file states **scope, explicit non-goals, and
> acceptance criteria** per Project-Playbook §2. When the two disagree, the capstone spec wins for
> product definition; this file governs build scope.

## 1. Goal
Ship a working **concierge agent** (Gemini + ADK, Cloud Run) that lets a 6th-grade AZ math teacher
ask natural-language questions about her students, curriculum, and communications, and get
standards-aligned, human-in-the-loop assistance. Submit to the Kaggle Concierge-Agents track by
**2026-07-06**.

## 1a. Delivered so far (Session 1, 2026-06-20)
- **Nova Voice Console** (`web/`) — talk to Nova in the browser via the **Gemini Live API**;
  arc-reactor orb in Karrie's palette, hands-free, mobile-first, speaker-aware, security-hardened.
  This is the "meet Nova" experience / first piece of Block 5 (Deployment + UX). Runs locally; Cloud
  deploy is Session 2.
- **TeacherMind data agent** (`agent/`) — already implements grade trends, at-risk flagging, standards
  mapping, Canvas, parent drafting (generic voice; not yet Nova-wired or connected to the console).

## 2. In scope (v1)
- Read a Synergy **CSV grade export** and normalize it.
- Map assignments/grades to **AZ Math Standards** (6.RP / 6.NS / 6.EE / 6.G / 6.SP).
- **At-risk flagging** with Major-Cluster priority rule.
- **Parent-communication drafting** (School-Net-ready, never auto-sent).
- Pull **Canvas** assignments/modules via REST API.
- **Wire the Nova persona** into the agent (`agent/agent.py` `SYSTEM_PROMPT` + `communication_drafter.py`),
  which are currently generic — warm, "I can…", "Oops!", Socratic. See persona research.

## 3. Explicit NON-goals (what we will NOT build in v1)
- ❌ No autonomous sending of any parent/family communication — drafts only.
- ❌ No write-back to Synergy, Canvas, or School-Net — read + draft only.
- ❌ No storage of real student PII in the repo or in source control (see PII rule below).
- ❌ No student-facing tutoring UI in v1 (Nova assists the *teacher*).
- ❌ No multi-teacher / multi-school support in v1 (single teacher).
- ❌ No proficiency-prediction ML model in v1 (deferred — most PII-sensitive block).

## 4. Candidate later capabilities (from Jim's notes — design separately)
1. **DOK small-group activity & assessment builder** (Depth-of-Knowledge leveled).
2. **Homework generator** seeded from her workbook patterns.
3. **Proficiency model** — infer current student levels to target the above (FERPA-heavy; design last).
4. **Cloud deployment + phone/web interface** on the Google Cloud agent layer.

(Brainstorming decomposed the program into 5 blocks: Knowledge base → Homework gen → DOK builder →
Proficiency model → Deployment/UX. Recommended first slice: **Knowledge base + Homework generator**,
prototyped before cloud. Paused pending Jim's pick — resume in `prompts/session-1-kickoff.md`.)

## 5. Acceptance criteria (v1 — "done" when these pass)

> **Status:** a working v1 in `agent/` already implements grade loading, at-risk flagging, standards
> mapping, Canvas tools, and parent drafting — so several items below are likely already met. Verify
> each against the running agent; the main *open* item is wiring in Nova's voice and confirming
> synthetic-data-only.
- [ ] Agent loads a sample (synthetic, PII-free) grade CSV and answers "who's struggling in Period N?"
- [ ] Every at-risk flag cites the specific assignment(s) that triggered it (explainable).
- [ ] Assignment→standard mapping shows its confidence and is teacher-correctable.
- [ ] Parent draft is returned as editable text, never sent; includes student situation + home support.
- [ ] Canvas tool returns upcoming assignments for a course.
- [ ] All sample/test data is synthetic — no real student PII anywhere in the repo or git history.
- [ ] Runs locally; deployable to Cloud Run.

## 6. PII / FERPA rule (non-negotiable)
No real student names, IDs, grades, attendance, or [REDACTED]/medical data in the repo or git history. Use
**synthetic** data for all tests/demos. The Karrie-derived persona research is gitignored/local-only
until PII-scrubbed. See `AGENTS.md` and `README.md`.

## 7. Open decisions for Session 1 (max-3 rule)
1. Product name **TeacherMind** vs. agent name **Nova** — keep both (product=TeacherMind, agent=Nova)?
2. First build slice — confirm "Knowledge base + Homework generator" or pick another block.
3. Prototype-in-Claude-Code-then-port-to-ADK, or build directly in ADK from the start?
