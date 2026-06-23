# Design Recommendations — Curriculum Awareness, DOK/Progress, Multi-Agent ADK + MCP

**Date:** 2026-06-21 · **Status:** recommendation for review · **Author:** Jim + Nova
**Scope:** the feature push Karrie wants this year (homework + DOK thought-partner), curriculum
awareness, anonymous progress tracking, the Drive intake path, and how to land the
**multi-agent ADK** and **MCP** course concepts the capstone is judged on.

---

## The one idea that ties it all together

**Make Google Drive the data backbone, and expose it through one MCP server.** Every hard
problem here — "how does Nova know what's next," "how do we track progress without Canvas," "how
does Karrie feed data post-submission" — collapses into the same answer: a small set of
**structured files in Nova's Drive** that one **MCP server** reads and writes. That server then
becomes the single backbone both the voice console and the data agent talk to (which also fixes
the "two disconnected faces" gap from the readiness assessment).

This honors the North Star: Karrie just opens a folder. No Canvas API required for submission.

---

## 1. Curriculum awareness — "what is Karrie teaching now, and next?"

**Recommendation: a Pacing Sheet in Drive (single source of truth).** One Google Sheet (or
`pacing.json`) under `Nova Teaching Assistant / Curriculum / <year>/`, one row per week:

| week | start_date | unit | topic | current_standards | review_standards | track |
|------|-----------|------|-------|-------------------|------------------|-------|
| 12 | 2026-11-02 | Unit 4 | Equations | 6.EE.B.5, 6.EE.B.6 | 6.NS.B.3, 6.RP.A.2 | both |

Nova derives "current week" from today's date and reads that row. This is the missing input that
the **already-built** `generate_week_spec(current_topic, current_standards, review_standards, …)`
needs — it takes exactly these fields today, hand-fed on the CLI. The Pacing Sheet just supplies
them automatically, and gives Nova "what's next" for free (next row).

Seed it from the existing `docs/karrie_profile/05_scope_sequence.md` (the enVision sequence is
already analyzed). Karrie edits the sheet when she reorders a unit — zero new tools to learn.

*Why not Canvas for this?* Canvas would be the "real" source but it's the hardest integration and
not needed: the pacing of a year is stable and small. Drive sheet now; Canvas later as an
enrichment (see §5).

---

## 2. DOK assessments & group activities — the headline new feature

Build `generate_dok_activity` as a **sibling of the spiral homework generator**, reusing the same
split-thinking-from-drawing architecture that already works:

- `models.py` → add `DOKActivitySpec` (items tagged `dok_level` 1–3, +4 optional, each with
  `standard_code`, `prompt`, `answer`/`rubric`, `group_role`).
- `generator.py` → `generate_dok_activity(standard, dok_levels[], group_size, format)`; prompt
  embeds the DOK verb-cue table (already in the Nova design spec §2) and **self-checks** items
  against the verb cues before returning (catches "this 'DOK 3' is really recall").
- `renderer.py` → activity card / small-group set + answer key (xlsx or Doc).
- Save to `02_Generated / Assessments_DOK / <topic>/` (folder layout already specced).

**DOK ladder** (a 1→2→3 progression for one standard) is the differentiation payload Karrie
asked for — it lets her hand different groups different depths of the same standard.

The **thought-partner** layer is the conversational front (Nova persona) that clarifies one
question Socratically, then calls homework or DOK generation grounded in the Pacing Sheet + the
knowledge base. This is the agent loop, not a new tool.

---

## 3. Anonymous progress tracking — placeholders now, real data next year

FERPA forbids real student data in the repo or any deployed surface, and Canvas/Synergy is
blocked. So design the **contract** now, populate it later.

**Pseudonymization from day one.** Students are stable aliases (`P2-07`), never names. A
mapping file, if one ever exists, stays local/private and never reaches the agent or repo.

**Mastery store** — one sheet under `Nova Teaching Assistant / Progress / <year>/`:

| alias | period | standard_code | date | score | source |
|-------|--------|---------------|------|-------|--------|
| P2-07 | 2 | 6.NS.A.1 | 2026-09-08 | 0.55 | diagnostic |

- **Initial/anonymous baseline testing:** `generate_diagnostic(standard|unit)` emits a short,
  DOK-tagged pre-assessment; Karrie records results into the mastery sheet (anonymously). That's
  your "anonymous initial testing" placeholder — defined and demoable on synthetic data now.
- **Progress reporting:** point the **existing** analytics tools — `get_class_standard_gaps`,
  `analyze_grade_trends`, `get_at_risk_students`, `draft_class_digest` — at the mastery sheet
  instead of a Synergy CSV. Same proven analytics, anonymous source. This is a clean swap, and it
  retires the dependency on Canvas/Synergy for the submission.

For the capstone demo: synthetic aliases + scores show the full loop (diagnose → record →
report → target homework/DOK at the gaps). Real population happens as next year progresses.

---

## 4. The Drive intake path (the post-submission on-ramp)

Adopt the `00_Inbox_from_Karrie/` folder already in the design spec as Nova's manual on-ramp,
and support three low-friction inputs:

1. **Drop a CSV** (Synergy export or a scores sheet) → `load_grade_export` already parses CSV;
   normalize into the anonymous mastery store.
2. **Edit the mastery Sheet inline** in Drive (no upload, no tool) — the zero-learning-curve path.
3. **Tell Nova** ("Period 2 struggled on the 6.NS quiz") → Nova writes a mastery update.

This makes Canvas optional: Karrie feeds Nova through Drive on her schedule. Canvas becomes a
post-submission upgrade, not a blocker.

---

## 5. Multi-agent ADK — recommended design (course concept #1)

Use ADK's **orchestrator + specialists** pattern (root `LlmAgent` with sub-agents, or specialists
exposed as `AgentTool`s). You already started this — `agents/prompts/00-orchestrator.md` exists;
formalize it. Recommended 4 agents, each owning a real job (not agents for their own sake):

```
            ┌──────────────────────────┐
            │   Nova  (root / thought   │  ← persona, clarifies, routes
            │   partner orchestrator)   │
            └────┬───────┬───────┬──────┘
                 │       │       │
       ┌─────────▼──┐ ┌──▼─────┐ ┌▼───────────┐
       │ Homework   │ │  DOK / │ │ Progress / │
       │ specialist │ │ Assess │ │ Insights   │
       └─────┬──────┘ └───┬────┘ └─────┬──────┘
             └────────────┴────────────┘
                          │ all read/write via
                   ┌──────▼───────┐
                   │ Curriculum/  │  (Pacing Sheet, KB, standards)
                   │ Drive MCP    │
                   └──────────────┘
```

- **Nova (root):** conversation + persona + routing. The only agent Karrie "talks to."
- **Homework specialist:** wraps the existing spiral generator; its own few-shot/style prompt.
- **DOK/Assessment specialist:** §2; its own DOK verb-cue self-check prompt.
- **Progress/Insights specialist:** reads the mastery store; reuses the analytics tools.

Why specialists beat one mega-prompt: each gets a tighter, higher-quality prompt and few-shot set,
and it's a genuine, demonstrable multi-agent system (the Day-1/Day-3 factory/orchestrator model).
Keep it to these 3–4; resist adding more.

A Curriculum/Pacing lookup can be a 5th agent or just a tool on the MCP server — **make it a tool,
not an agent** (it's deterministic retrieval, no reasoning needed).

---

## 6. MCP servers — recommended design (course concept #2)

**Build one MCP server now; stub a second for later.**

**A) Nova Curriculum/Drive MCP (build for submission).** Wrap the Drive backbone as MCP tools +
resources so it's reusable by both the console and the agent (and demonstrates MCP cleanly):
- `get_current_pacing()` / `get_next_pacing()` — reads the Pacing Sheet (§1).
- `list_knowledge_base()` / `get_style_exemplars()` — the homework/DOK few-shot source.
- `save_draft(content, kind, topic)` / `promote_to_approved(file_id)` — generated-work I/O.
- `record_mastery(rows)` / `get_progress(period?, standard?)` — the anonymous store (§3).
- Resources: the AZ standards JSON and the DOK model (natural MCP *resources*, not tools).

This replaces the bespoke Google API code currently inline in `drive_store.py` with a clean,
standard interface — exactly the Day-2 interoperability point, and it unifies the product.

**B) Canvas MCP (stub now, finish post-submission).** Wrap `canvasapi` behind MCP tools
(`get_assignments`, `get_modules`, `get_roster`). Build the interface against the existing
sample data now; swap in real Canvas (OAuth) after submission. When Canvas access is solved it
plugs in as just another connector — which is the whole promise of MCP. **This is the right home
for the "reaching Canvas is a challenge" work:** make it a pluggable MCP boundary so the hard part
is isolated and deferrable.

---

## 7. Course-concepts scorecard (capstone needs ≥3)

With the above you can demonstrate **four**, with room to spare:

1. **Multi-agent ADK** — orchestrator + homework/DOK/progress specialists (§5).
2. **MCP server** — the Curriculum/Drive backbone (§6), Canvas stub for interoperability.
3. **Agent Skills** — homework & DOK generators as progressive-disclosure capabilities.
4. **Security/eval** — already hardened (the `/ws` work); **or** SDD — specs already drive the build.

---

## 8. Recommended sequencing (15 days to 2026-07-06)

**For submission — build the loop end-to-end on synthetic/anonymous data:**
1. Pacing Sheet + `get_current_pacing` (small, unlocks everything).
2. Curriculum/Drive **MCP server** wrapping Drive + pacing + mastery + KB.
3. **DOK generator** (the headline feature) as a specialist.
4. Wire Nova as an **ADK orchestrator** over Homework + DOK + Progress specialists.
5. Anonymous mastery store + progress reporting (reuse existing analytics).

**Post-submission (next school year):** Canvas MCP with real OAuth; live diagnostic population
with anonymized real students; Inbox-driven sample intake; scheduled weekly digest; embedded
figures/images in generated work.

**Caution:** this is an ambitious 15 days *if* you also deploy. Recommend picking the submission
spine above and treating deploy + voice-wiring as the parallel must-haves; everything else is
post-publish. Don't add capabilities beyond the DOK builder before the deadline.
