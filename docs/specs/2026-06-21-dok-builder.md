# Spec — DOK Assessment & Group-Activity Builder (v1)

**Date:** 2026-06-21 · **Status:** DRAFT for review · **Author:** Jim + Nova
**Part of:** the homework/DOK feature push (Nova design spec §1–2). The headline new capability
Karrie wants this year.
**Pattern:** sibling of the working spiral homework generator — same split-thinking-from-drawing.
**Depends on:** Pacing (for standards/topic), DOK model resource. **Saves via:** Drive/Curriculum MCP.

## Goal
Generate **small-group activities and assessments tagged by Webb's Depth of Knowledge (DOK 1–3,
4 optional)**, each aligned to an AZ Math standard, with answer keys/rubrics — so Karrie can probe
how deeply students understand a standard and differentiate by group. Build a **DOK ladder** (a
1→2→3 progression for one standard) for small-group differentiation. Editable output in Drive,
human-in-the-loop. Ship by **2026-07-06**.

## Decisions (proposed → confirm)
- **Generate, don't bank.** Gemini writes the items from the standard + DOK level, grounded in the
  AZ standards data and (when available) Karrie's style exemplars. (Same choice as homework v1.)
- **DOK source of truth = the `dok://webb-model` resource** (verb-cue table), so levels are
  consistent everywhere. Verbs per level: DOK1 recall/identify/calculate; DOK2
  classify/compare/predict/infer; DOK3 assess/hypothesize/justify/conclude; DOK4 (optional)
  design/synthesize/critique.
- **Self-check before save:** the generator validates each item's language against the level's verb
  cues and rejects/regenerates mismatches (a "DOK 3" that is really recall fails the check).
- **Output format: default `.xlsx`** (CONFIRMED 2026-06-21) — matches the homework generator and
  keeps Karrie in Excel where she already authors. An **activity set** (group cards) + a separate
  **answer key/rubric** sheet. Google Doc export is a later option, not v1. Figure placeholders as
  labeled text (no embedded images in v1), matching homework v1.
- **Real-world contexts, fictional names only** (PII-safe), rotating — same rule as homework.

## Data model
`models.py` adds:
- `DOKItem`: `{ dok_level:1|2|3|4, standard_code:str, prompt:str, answer:str,
  rubric?:str, group_role?:str, figure_note?:str }`
- `DOKActivitySpec`: `{ standard_code:str, topic:str, dok_levels:[int], group_size:int,
  format:str, items:[DOKItem] }`
- Validation: every item's `dok_level` ∈ requested levels; `standard_code` valid; ≥1 item per
  requested level; a "ladder" request yields exactly one ascending chain per standard.

## Architecture (`agent/tools/dok_builder/`)
1. `models.py` — `DOKItem`, `DOKActivitySpec` (above).
2. `generator.py` — `generate_dok_activity(standard, dok_levels, group_size=4, format="xlsx",
   topic=None, _call=_call_gemini) -> DOKActivitySpec`. Prompt embeds the verb-cue table + 1–2
   style exemplars; **validates + self-checks** verb alignment; one retry then clear error (mirrors
   `spiral_homework/generator.py`).
3. `ladder.py` — `generate_dok_ladder(standard) -> DOKActivitySpec` (1→2→3[→4] chain for one
   standard, for differentiated small groups).
4. `renderer.py` — deterministic writer: a group-activity sheet (one card per group/level) + a
   separate **answer key/rubric**; openpyxl (xlsx) now, Doc export later. Pure/offline/testable.
5. Orchestrator/CLI — `python -m agent.tools.dok_builder --standard 6.RP.A.3 --levels 1,2,3
   --group-size 4 [--ladder] [--no-upload]`; runs generate → render → save via the MCP
   `save_draft` (folder `02_Generated / Assessments_DOK / <topic>/`) with local fallback.

## Data flow
Nova (thought-partner clarifies one question) → `generate_dok_activity` grounded in standards +
exemplars → `DOKActivitySpec` (self-checked) → `render` → `.xlsx`/Doc → MCP `save_draft` → Drive
`02_Generated/Assessments_DOK/<topic>` (shared) → Karrie reviews/edits → promotes to `03_Approved`.

## Error handling
- Verb-cue self-check fails for an item → regenerate that item (bounded retries), else flag it in
  the output as "review DOK level," never silently mis-tag.
- Ambiguous request (no level given) → Nova asks one Socratic clarifying question (don't over-generate).
- No style exemplars yet → generate from standards + DOK model and note that style-matching improves
  once samples are in the KB (don't blindly guess her format).
- Save failure → keep local file, report path (reuse the homework local-fallback pattern).

## Testing (TDD)
- `DOKActivitySpec` validation: level membership, ≥1 item/level, ladder = ascending chain, valid codes.
- Verb-cue self-check: synthetic items with wrong-level verbs are caught; correct ones pass.
- Generator against a **canned** Gemini response → valid spec; malformed → retry then error.
- Renderer (no network): fixed spec → read `.xlsx` back, assert items in right cells + a present
  answer key + DOK labels.
- All offline in CI; live generation is a manual smoke test.

## Acceptance criteria (v1 "done")
- [ ] `generate_dok_activity(standard, [1,2,3])` returns items correctly tagged per level, each
      aligned to the standard, with an answer key/rubric.
- [ ] `--ladder` produces a single 1→2→3 progression for one standard.
- [ ] Verb-cue self-check rejects a mis-leveled item in tests.
- [ ] Output renders as an editable activity set + answer key; figure needs are labeled placeholders.
- [ ] Saved to Drive `02_Generated/Assessments_DOK/<topic>` via the MCP (local fallback on failure).
- [ ] No student PII; fictional names only; tests synthetic; model + renderer tests pass.

## Out of scope (v1) / later
- ❌ Embedded figure images (text + placeholders for now).
- ❌ Auto-grading student responses; auto-distribution to students.
- ❌ Adaptive selection of DOK level from a student's mastery (that's the Progress specialist
      feeding this later — design once the mastery store has data).
