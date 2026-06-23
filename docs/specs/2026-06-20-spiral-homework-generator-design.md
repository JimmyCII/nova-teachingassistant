# Spec — Spiral Homework Generator (v1)

**Date:** 2026-06-20 · **Status:** approved design → ready for implementation plan
**Part of:** the homework generator (increment 1) in
`docs/superpowers/specs/2026-06-20-nova-teaching-assistant-design.md`.
**Knowledge base it builds on (local-only):** `docs/karrie_profile/homework/` —
`homework_style_guide.md`, `homework_exemplars.md`, `homework_templates.md`.

## Goal
Generate Karrie's **weekly Spiral Review homework** as an **editable Excel (`.xlsx`)** file in her
format, so she can open it in Excel and tweak it. Ship a **solid, publishable v1** by the Kaggle
deadline (2026-07-06) and **iterate** as Karrie asks for more.

## Decisions (locked)
- **Problem source:** Nova/**Gemini generates** the problems from the week's current topic + review
  standards, grounded in the style guide + exemplars. (Not a hand-authored bank.)
- **Math/figures (v1):** **editable text/Unicode math** in cells; **labeled placeholders** where a
  figure is needed (number line, coordinate plane). **No embedded images**, no decorative clip art in
  v1 — Karrie adds those in Excel if she wants.
- **First milestone:** a **standalone generator → `.xlsx`** (runnable CLI), producing **regular +
  accelerated** versions, so Karrie can react to the format before it's wired into Nova.
- It's a **Python tool** Nova can call later — not a Claude Code `SKILL.md` (Nova runs as its own
  agent).
- **Home for the work:** each `.xlsx` is saved to **Nova's Google Drive**
  (`nova-assistant@example.com`) via the Drive API (OAuth `drive.file` scope — the app only sees
  files it creates). Folder layout **mirrors Karrie's year structure**:
  `Nova Teaching Assistant / Homework / <school-year> / Drafts | Approved`. Nova drops drafts in
  **Drafts**; Karrie moves keepers to **Approved**. The root folder is **shared with Karrie**.

## Architecture — split "thinking" from "drawing"
New module `agent/tools/spiral_homework/`:
1. **`models.py` — `WeekSpec`** (pydantic). One week = `{ due_date, track, boxes[] }`; each box =
   `{ day: Mon|Tue|Wed|Thu, slot, type: "computation"|"word_problem"|"brain_break"|"figure_placeholder",
   role: "current"|"review", standard_code, text, figure_note? }`. Target ~14–16 boxes, 4 per day.
2. **`generator.py` — `generate_week_spec(current_topic, current_standards, review_standards, due_date, track) → WeekSpec`.**
   Calls Gemini with a prompt that embeds the style guide + 1–2 few-shot exemplars; instructs the
   ~50/50 spiral mix, 2–4 real-world word problems (rotating fictional names; "Show your work" /
   "Write and solve"), one "Brain Break!". Parses + **validates** the JSON into `WeekSpec`.
3. **`renderer.py` — `render_xlsx(week_spec, out_path) → Path`.** Deterministic **openpyxl** writer:
   header row (`Name ____ | Spiral Review Homework | Due M/D`), 4 day columns, a bordered box grid,
   each box's text (Unicode math), figure placeholders as labeled text, tall rows for "show your
   work." Pure, offline, fully testable.
4. **`drive_store.py` — `upload_to_drive(local_path, school_year, status="Drafts") → drive_link`.**
   Ensures `Nova Teaching Assistant / Homework / <school-year> / Drafts` exists (creating folders as
   needed), uploads the `.xlsx`, and ensures the **root folder is shared with Karrie**. OAuth
   `drive.file`; refresh token cached locally (gitignored). A thin wrapper so the rest of the tool
   never touches the Drive API directly (and stays testable by mocking this unit).
5. **`__main__.py` / orchestrator — `generate_spiral_homework(...) → result`** and a CLI:
   `python -m agent.tools.spiral_homework --topic "Equations" --due 2/6 --review 6.NS.B.3,6.RP.A.2 --track both [--no-upload]`.
   Runs generate → render → upload (unless `--no-upload`); `--track both` emits regular + accelerated;
   returns local path(s) **and** Drive link(s).

## Data flow
caller (CLI now; UI button / scheduler later) → `generate_week_spec` (Gemini) → validated `WeekSpec`
→ `render_xlsx` (openpyxl) → local `.xlsx` → `upload_to_drive` → **Nova's Drive
`Homework / <year> / Drafts`** (shared with Karrie) → **Karrie opens & edits in Excel, then moves
keepers to Approved** (human-in-the-loop).

## Google Drive home (Nova's account)
- **Account & auth:** `nova-assistant@example.com`. OAuth 2.0 **desktop** flow, scope
  **`drive.file`** (least privilege — only files the app creates). A one-time browser consent
  (signed in as Nova's account) yields a refresh token cached to a **gitignored** local file
  (`.nova_drive_token.json`); subsequent runs are non-interactive.
- **Setup prerequisite (Jim, one-time):** in Google Cloud project `gen-lang-client-0232400708`,
  enable the Drive API and create an **OAuth client ID (Desktop)**; download `client_secret.json`
  (gitignored). First run opens the consent screen — approve as Nova's account.
- **Folder structure (created on demand):**
  `Nova Teaching Assistant / Homework / <school-year> / {Drafts, Approved}`. New files go to
  **Drafts**; Karrie promotes keepers to **Approved**. `<school-year>` is derived from the due date
  (an Aug–Jul academic year → e.g. a 9/12 due date ⇒ `2025-2026`) or set explicitly via `--year`.
- **Sharing:** the tool shares the root `Nova Teaching Assistant` folder with Karrie's email (writer)
  so it shows up in her Drive.
- **New deps:** `google-api-python-client`, `google-auth`, `google-auth-oauthlib` (record in
  `DEPENDENCIES.md`).

## Error handling
- Generator validates Gemini's output against `WeekSpec`; **one retry** on malformed/short output,
  then a clear error message. Never silently ship an empty sheet.
- Renderer is pure/offline; if the spec has fewer than the target boxes, it renders what's there and
  leaves the rest blank.
- API key from `.env` (`GOOGLE_API_KEY`); fail with a clear message if missing.
- **PII:** the generator prompt forbids real student data and uses neutral fictional names only.
- **Drive:** if upload fails or auth isn't set up, **keep the local `.xlsx`** and report its path +
  the reason (and how to run the one-time consent). Never lose the work to a Drive error. `--no-upload`
  skips Drive.

## Testing (TDD — write tests first)
- **Renderer (no network):** given a fixed `WeekSpec`, read the `.xlsx` back with openpyxl and assert
  the header text, 4 day-column headers, expected box texts in the right cells, and borders present.
- **`WeekSpec` model:** validation — box count/range, allowed `type`/`role`, required fields, the
  spiral mix has both current + review roles.
- **Generator:** against a **canned/mocked** Gemini response → asserts a valid `WeekSpec`; malformed
  response → triggers retry then error. (Optional live smoke test, not in CI.)
- **Drive store:** unit-test folder-path resolution, filename, and ensure/upload/share against a
  **mocked** Drive client (no network) — assert it targets `…/<year>/Drafts` and shares the root.
  Live Drive run is a manual smoke test, not in CI.

## Acceptance criteria (v1 "done")
- [ ] `python -m agent.tools.spiral_homework --topic ... --due ... --review ...` writes a `.xlsx`.
- [ ] The `.xlsx` opens in Excel as a 4-column Mon–Thu bordered grid with the standard header.
- [ ] Content shows a **spiral mix** (both current-topic and review boxes), 2–4 word problems, one
      Brain Break.
- [ ] `--track both` produces a **regular** and an **accelerated** file (acc has less basic
      computation / more conceptual).
- [ ] Figure placeholders are clearly labeled where a visual is needed.
- [ ] The `.xlsx` is uploaded to Nova's Drive under `Homework / <year> / Drafts`, the tool returns the
      Drive link, and the root folder is shared with Karrie. (`--no-upload` writes local-only.)
- [ ] If Drive auth/upload fails, the local `.xlsx` is still produced and its path reported.
- [ ] Renderer + model + drive-store (mocked) tests pass; generator test passes against a mocked response.
- [ ] No real student data anywhere; tests/data synthetic.

## Out of scope (v1) / Future increments
- ❌ Embedded images (typeset-math images, figures, decorative clip art) — v1 uses text + placeholders.
- ❌ **UI button** in the Nova console to trigger generation — Phase 2.
- ❌ **Date/time-aware scheduling** (Nova knows "today," auto-builds "next week's" spiral) — Phase 2.
- ❌ Wiring as a Nova ADK tool / voice trigger — after format is validated with Karrie.
- ❌ Pulling problems from a curated bank — LLM generation only in v1.

## Delivery philosophy
Ship a **solid, publishable v1** (the above acceptance criteria) by the deadline; treat images, UI
trigger, scheduling, and Nova-tool wiring as **post-publish iterations** driven by what Karrie
actually needs.
