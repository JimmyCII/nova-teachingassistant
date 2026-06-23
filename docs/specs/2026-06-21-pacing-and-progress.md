# Spec — Pacing Sheet + Anonymous Progress Store (v1)

**Date:** 2026-06-21 · **Status:** DRAFT for review · **Author:** Jim + Nova
**Part of:** the feature push (curriculum awareness + progress tracking). Feeds the Homework and
DOK generators and the Progress/Insights specialist.
**Depends on:** nothing (pure data + analytics). **Feeds:** Drive/Curriculum MCP, DOK builder,
ADK orchestrator.

## Goal
Give Nova two things she lacks today: (1) **knowledge of what Karrie is teaching now and next**,
and (2) **a place to track how students are doing over the year** — both anonymous, both living in
Drive, both demoable on synthetic data by the **2026-07-06** deadline. No Canvas/Synergy required.

## Decisions (proposed → confirm)
- **Pacing source of truth = one sheet in Drive**, `Nova Teaching Assistant / Curriculum / <year> /
  pacing.(csv|xlsx)`. One row per week. Karrie edits it in place when she reorders a unit.
- **Current week = derived from today's date** against the `start_date` column (the row whose week
  contains today). "Next" = the following row.
- **Progress = one anonymous mastery sheet** in Drive, `… / Progress / <year> / mastery.(csv|xlsx)`.
  Students are **stable aliases** (`P2-07`), never names. Any alias→name map is local-only and
  never enters the agent, repo, or any deployed surface (FERPA).
- **Reuse, don't rebuild analytics.** Repoint the existing `get_class_standard_gaps`,
  `analyze_grade_trends`, `get_at_risk_students`, `draft_class_digest` at the mastery sheet by
  normalizing it into the same shape `load_grade_export` already returns.
- **Diagnostic placeholder:** `generate_diagnostic(unit|standard)` emits a short DOK-tagged
  pre-assessment whose results Karrie records into the mastery sheet (the "anonymous initial
  testing" entry point). Generation reuses the DOK builder; this spec just defines the data sink.

## Data model
**Pacing row** (`PacingWeek`, pydantic):
`{ week:int, start_date:date, unit:str, topic:str, current_standards:[str],
   review_standards:[str], track:"regular"|"accelerated"|"both", notes?:str }`

**Mastery row** (`MasteryEntry`, pydantic):
`{ alias:str, period:str, standard_code:str, date:date, score:float(0..1),
   source:"diagnostic"|"quiz"|"observation"|"import", dok_level?:1|2|3|4 }`

## Architecture
New module `agent/tools/curriculum/`:
1. `models.py` — `PacingWeek`, `MasteryEntry` (validation: score 0–1, valid AZ standard codes,
   non-empty standards lists).
2. `pacing.py` — `load_pacing(path|drive) -> list[PacingWeek]`; `current_week(pacing, today) ->
   PacingWeek`; `next_week(pacing, today) -> PacingWeek`. Pure, date-driven.
3. `progress.py` — `load_mastery(...) -> list[MasteryEntry]`; `record_mastery(rows)`;
   `to_grade_data(mastery) -> dict` adapter that emits the **exact shape** the existing analytics
   tools consume, so `get_class_standard_gaps` / `analyze_grade_trends` / `get_at_risk_students` /
   `draft_class_digest` work unchanged on the anonymous store.
4. (Drive I/O is **not** in this module — it goes through the Drive/Curriculum MCP. For local dev,
   `pacing.py`/`progress.py` read local CSV/xlsx so they're testable offline.)

## Data flow
- **Homework/DOK:** caller asks Nova for "this week's homework" → `current_week()` supplies
  `topic / current_standards / review_standards` → existing `generate_week_spec(...)` (no change).
- **Progress:** Karrie records scores (Drive edit / CSV drop / "tell Nova") → `record_mastery` →
  `mastery.csv` → `to_grade_data` → existing analytics → at-risk flags & digest, now standard-by
  standard and anonymous.

## Error handling
- No pacing row for today (gap/summer) → return the nearest upcoming row and say so; never crash.
- Unknown/invalid standard code in either sheet → skip the row, warn, continue (don't fail the batch).
- Empty mastery store → analytics return "no data yet," not an error (first-run state).
- **PII guard:** reject any mastery import whose `alias` looks like a real name (heuristic: contains
  a space + capitalized token) — force aliasing. No names ever persisted.

## Testing (TDD)
- `current_week` / `next_week`: fixed pacing + several "today" dates → correct rows, gap handling.
- `MasteryEntry` validation: score range, alias guard, standard-code validation.
- `to_grade_data` adapter: a known mastery set produces the shape the analytics tools expect, and
  `get_class_standard_gaps` over it returns the expected per-standard averages.
- All offline (local CSV fixtures); no Drive/network in CI.

## Acceptance criteria (v1 "done")
- [ ] A synthetic `pacing.csv` drives `current_week(today)` → correct topic + standards.
- [ ] `generate_week_spec` can be fed entirely from the pacing row (no hand-entered standards).
- [ ] A synthetic anonymous `mastery.csv` flows through `to_grade_data` into the existing analytics,
      producing per-standard gaps, at-risk flags, and a class digest — all by alias, no names.
- [ ] `generate_diagnostic(unit)` produces a short DOK-tagged pre-assessment (delegates to DOK builder).
- [ ] PII guard rejects a name-shaped alias; no real student data anywhere; tests synthetic.

## Out of scope (v1) / later
- ❌ Real Synergy/Canvas ingest (post-submission; arrives via the Inbox/CSV path + Canvas MCP).
- ❌ Auto-derived school calendar / holidays (manual `start_date` column for v1).
- ❌ Longitudinal multi-year trend charts; proficiency-prediction ML (separate, later block).
