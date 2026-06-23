# Spec — Nova Teaching Assistant: Core Capabilities (Homework · DOK Activities · Thought Partner · Drive Repository)

**Date:** 2026-06-20 · **Status:** DRAFT for review · **Author:** Jim Cockerham (+ Claude)
**Relationship:** Defines Nova's **primary role** (content generation + thought partner). Complements
the existing **TeacherMind** data tools (`agent/`, grades/standards/Canvas/parent-comms in
`CAPSTONE_SPEC.md`). Same agent (**Nova**); this spec adds the teaching-assistant capability set.

> **Implementation status (2026-06-20):** Nova's **voice/console front-end** is built (`web/`, the
> "thought partner" surface — see `prompts/session-1-kickoff.md`). The **homework generator**, **DOK
> builder**, **knowledge base**, and **Drive repository** in this spec are **NOT built yet** — they're
> the capability track for an upcoming increment (after the Cloud deploy in Session 2). Needs Karrie's
> homework/workbook samples + Drive OAuth.

> **North Star (governs every decision):** an easy assistant Karrie can use with **zero learning
> curve** — it meets her in tools she already uses (Google Docs/Drive, chat/voice), **saves her
> time**, and **deepens her impact** with students. Human-in-the-loop on everything she'll use.

---

## 1. Primary role (what Nova does)
1. **Generate homework assignments** for 6th-grade Arizona Math, **guided by the teacher**. Nova
   proposes; Karrie steers. Output matches her style (enVision-aligned, real-world anchored,
   "Try it!" rhythm, her numbering/formatting).
2. **Create small-group activities & assessments that test Depth of Knowledge (DOK).** Differentiated
   by DOK level so Karrie can probe how deeply students understand a standard.
3. **Be a thought partner.** Conversational mode where Karrie shares a need or challenge and Nova
   reasons *with* her (Socratic, in the Nova persona), then drafts the materials to match.

All three write their outputs to a **Google Drive repository** (Nova's account) for Karrie to review,
tweak, approve, and use.

## 2. Depth of Knowledge model (Webb's DOK — source: Progress Learning)
| DOK | Name | Student does | Verb cues |
|-----|------|--------------|-----------|
| **1** | Recall & Reproduction | retrieve facts, run a basic procedure | define, identify, calculate, recall, label |
| **2** | Skills & Concepts | apply concepts in multi-step problems | classify, compare, predict, infer, summarize |
| **3** | Strategic Thinking | reason & justify with evidence | assess, hypothesize, draw conclusions, argue |
| **4** | Extended Thinking | complex reasoning over time; novel application | analyze, create, design, synthesize, critique |

Nova tags every generated item with its DOK level and the AZ standard, and can build a **DOK ladder**
for one standard (a 1→2→3(→4) progression) for small-group differentiation.

## 3. Knowledge base — learn Karrie's style
Nova must generate **in Karrie's voice and format**, so it needs examples:
- **Samples needed:** Karrie's past homework assignments and workbook pages (enVision/Glencoe,
  her "Try it!" notes, real-world contexts). These live in her archive (`W:\Karrie school\Homework\`,
  `Lesson Plans\…\Homework\`, Eureka/enVision) — **PII-sensitive / gitignored**; ingest only
  curriculum content, never student data.
- **How she provides them (open question, see §8):** drop into a Drive `Inbox` folder, or we extract
  a PII-scrubbed sample set from the archive.
- **Use:** few-shot style-matching (and/or light RAG) so generated homework looks like *hers*, plus
  the AZ standards data already in `agent/data/az_math_6_standards.json`.

## 4. Output repository — Google Drive (account: `nova-assistant@example.com`)
Nova owns a Drive, shared with Karrie, with a predictable structure (zero learning curve — she just
opens a folder):
```
Nova Teaching Assistant/            (Drive root, owned by nova-assistant@example.com, shared → Karrie)
├── 00_Inbox_from_Karrie/           # she drops samples / requests here
├── 01_Knowledge_Base/              # curated, PII-free source material Nova learns from
│   ├── Homework_Samples/
│   ├── Workbook_Pages/
│   └── Standards_Reference/
├── 02_Generated/                   # Nova's drafts (dated, versioned)
│   ├── Homework/<Topic>/
│   ├── Small_Group_Activities/<Topic>/
│   └── Assessments_DOK/<Topic>/
├── 03_Approved/                    # Karrie moved it here = ready to use with students
└── 99_Archive/
```
- **Format default:** Google **Docs** (editable in place, zero learning curve). PDF export optional.
- **Account/auth:** OAuth 2.0 for `nova-assistant@example.com` with **Drive** scope (and **Gmail**
  later for notifications, per `docs/ideas.md` idea #1). Token stored locally (gitignored), least
  privilege. Personal Gmail is fine for the prototype; revisit Workspace if needed.

## 5. Architecture & components
New ADK tools (alongside the existing TeacherMind tools in `agent/tools/`):
- `generate_homework(standard|topic, num_problems, difficulty_mix, real_world_context, notes)` →
  homework doc in Karrie's style; saves to `02_Generated/Homework/<Topic>/`.
- `generate_dok_activity(standard, dok_levels[], group_size, format)` → small-group activity/assessment
  set tagged by DOK, with answer key/rubric; saves to `02_Generated/…`.
- `save_to_drive(content, folder_path, doc_name)` / `list_drive(folder)` → Drive I/O via Nova's account.
- (Thought-partner is the conversational layer — the agent loop + Nova persona — that calls the above
  and the existing data tools.)

**Persona:** all generation and conversation run in the **Nova** voice (`docs/karrie_profile/
06_nova_persona.md`, Part 2) — warm, "I can…", Socratic, "Oops!". (Wiring Nova into `SYSTEM_PROMPT`
remains the prerequisite from `session-1-kickoff.md`.)

## 6. Data flow
Karrie (chat/voice) → Nova *thought partner* clarifies the need → calls `generate_homework` /
`generate_dok_activity`, grounded in the **knowledge base** (her samples + AZ standards) → draft saved
to **Drive `02_Generated`** → Karrie reviews/edits → moves to `03_Approved` → uses with students.
**Human-in-the-loop at every outward step.**

## 7. Error handling
- No style samples yet → Nova asks Karrie to drop a few in `00_Inbox` (don't guess her format blindly).
- Ambiguous request → Nova asks one clarifying question (Socratic), doesn't over-generate.
- Drive auth/quota failure → fall back to writing a local file and tell Karrie.
- DOK mismatch → self-check generated items against the DOK verb cues before saving.

## 8. Open questions (decide before/at build)
1. **Sample sourcing:** Karrie drops samples in the Drive `Inbox`, **or** we extract a PII-scrubbed
   homework sample set from `W:\Karrie school\Homework\` for the knowledge base? (Latter is faster but
   needs a scrub pass.)
2. **Account scope:** `nova-assistant@example.com` personal Gmail for prototype — confirm OAuth
   consent + Drive scope is acceptable; Gmail scope now or later?
3. **Output format:** Google Docs only, or Docs + PDF? (Default: Docs.)
4. **Build order:** Homework generator as **increment 1**, DOK builder increment 2, thought-partner
   threads through both? (Recommended.)
5. **DOK 4 inclusion:** Progress Learning builds DOK 1–3; do we include DOK 4 (extended/project)? 6th
   grade can reach DOK 3 routinely; DOK 4 as optional enrichment.

## 9. Acceptance criteria (v1)
- [ ] `generate_homework` produces a 6th-grade AZ-Math homework set for a given standard/topic, in
      Karrie's format, saved to Drive, returned for review.
- [ ] Generated homework visibly reflects her style (real-world context, "Try it!" structure) when
      sample material is provided.
- [ ] `generate_dok_activity` produces a small-group set with items correctly tagged DOK 1–3 (4
      optional), each aligned to an AZ standard, with an answer key/rubric.
- [ ] Items save into the correct Drive folders under `nova-assistant@example.com`; Karrie can
      open and edit them.
- [ ] Thought-partner mode: Karrie can describe a need in plain language and Nova clarifies, then
      generates the right artifact — in the Nova voice.
- [ ] No student PII anywhere; all examples use generic names; knowledge-base ingest is curriculum-only.

## 10. Non-goals (v1)
- ❌ No auto-grading of student work; ❌ no auto-distribution to students; ❌ no student PII in
  generated items or the knowledge base; ❌ not replacing her curriculum (augments enVision);
  ❌ no proficiency-prediction model (separate, later block).

---
*Next per `superpowers:brainstorming`: Jim reviews this spec → on approval, `superpowers:writing-plans`
produces the increment-1 (homework generator) implementation plan.*
