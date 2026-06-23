# Spec — Nova Curriculum/Drive MCP Server (v1)

**Date:** 2026-06-21 · **Status:** DRAFT for review · **Author:** Jim + Nova
**Part of:** the data backbone. Demonstrates the **MCP** course concept and unifies the voice
console + data agent onto one shared data layer.
**Depends on:** Pacing + Progress backbone (data shapes). **Used by:** ADK orchestrator,
Homework specialist, DOK specialist, Progress specialist.

## Goal
Expose Nova's Drive backbone — **pacing, knowledge base, generated-work I/O, and the anonymous
mastery store** — as **one MCP server** with clean tools + resources, so every agent (and the
console) talks to the same standardized interface instead of bespoke Google API code. Ship a
working server by **2026-07-06** that runs locally over stdio and is wired into the agent.

## Why MCP here (course-concept fit)
- Replaces the Google API code currently inline in `agent/tools/spiral_homework/drive_store.py`
  with a standard, reusable boundary (Day-2 interoperability).
- One server, many clients: the data agent **and** the voice console both consume it → directly
  closes the "two disconnected faces" gap from the readiness assessment.
- Makes the later **Canvas MCP** a drop-in sibling (separate spec/stub).

## Build approach
- Use the **`mcp-builder` skill** + Python **FastMCP** (already in this repo's skill set).
- Transport: **stdio** for v1 (local, agent-embedded). HTTP/SSE is a later option for the deployed
  console.
- Auth: reuse the existing OAuth `drive.file` flow from `drive_store.py` (token cached, gitignored).
  Least privilege — the app only sees files it creates.

## Tools (MCP)
| Tool | Signature → returns | Notes |
|------|--------------------|-------|
| `get_current_pacing` | `(today?) → PacingWeek` | reads `Curriculum/<year>/pacing`; "what are we on" |
| `get_next_pacing` | `(today?) → PacingWeek` | "what's next" |
| `list_knowledge_base` | `(kind?) → [file meta]` | homework/DOK style exemplars |
| `get_style_exemplars` | `(kind, n=2) → [content]` | few-shot source for generators |
| `save_draft` | `(content|local_path, kind, topic, track?) → drive_link` | writes to `02_Generated/<kind>/<topic>/`; **reuses** `upload_homework` folder logic |
| `promote_to_approved` | `(file_id) → drive_link` | move draft → `03_Approved/` (Karrie's review action; tool-assisted) |
| `record_mastery` | `(rows:[MasteryEntry]) → count` | append to `Progress/<year>/mastery`; PII guard |
| `get_progress` | `(period?, standard?) → grade_data` | returns the analytics-ready shape (via `to_grade_data`) |

## Resources (MCP)
| Resource URI | Content |
|--------------|---------|
| `standards://az-math-6` | `agent/data/az_math_6_standards.json` (read-only reference) |
| `dok://webb-model` | the DOK 1–4 verb-cue table (single source for the DOK builder) |
| `pacing://current` | current week as a resource (cheap context for the orchestrator) |

## Architecture
New `mcp/curriculum_server/` (separate from `agent/` so it can run standalone):
- `server.py` — FastMCP app; registers the tools/resources above.
- `drive.py` — thin adapter that **calls the existing** `drive_store.GoogleDriveClient` (don't
  duplicate the Drive API; wrap it). Adds folder paths for `Curriculum/`, `Progress/`, `02_Generated/`.
- `data.py` — loads standards JSON + DOK table for the resources.
- Reads/writes go through the `agent/tools/curriculum/` models (pacing/progress) so shapes stay
  consistent with the analytics tools.

## Data flow
agent/orchestrator (MCP client) → `get_current_pacing` → feeds generators → `save_draft` writes to
Drive `02_Generated` (shared with Karrie) → Karrie reviews → `promote_to_approved`. Progress:
`record_mastery` → mastery sheet; `get_progress` → analytics-ready data for the Progress specialist.

## Error handling
- Drive auth missing/expired → return a structured MCP error with the one-time-consent instructions;
  for `save_draft`, **fall back to a local file** and return its path (never lose generated work).
- Missing pacing/mastery sheet → create on first write; reads return an explicit "not set up yet."
- `record_mastery` runs the **PII guard** (reject name-shaped aliases) before any write.

## Testing
- Tool layer against a **mocked** DriveClient (the existing fake from `tests/spiral_homework/`):
  assert `save_draft` targets `02_Generated/<kind>/<topic>/`, `record_mastery` appends valid rows,
  `get_progress` returns the analytics shape. No network in CI.
- A live smoke test (manual, not CI): start the server, call each tool against Nova's real Drive.
- MCP contract test: server starts over stdio, lists the expected tools/resources.

## Acceptance criteria (v1 "done")
- [ ] `mcp/curriculum_server` starts over stdio and lists all tools + resources above.
- [ ] `get_current_pacing` returns the right week from a synthetic pacing sheet.
- [ ] `save_draft` writes an `.xlsx`/Doc to the correct Drive folder and returns a link (local
      fallback on auth failure).
- [ ] `record_mastery` + `get_progress` round-trip anonymous data into the analytics shape.
- [ ] The data agent consumes the server as an MCP client (one tool call end-to-end).
- [ ] No bespoke Drive API calls remain outside `drive_store.py`/this server; no PII; tests mocked.

## Out of scope (v1) / later
- ❌ HTTP/SSE transport + remote auth (after Cloud deploy).
- ❌ Canvas tools (separate **Canvas MCP** stub — its own spec).
- ❌ Write-back to Synergy/School-Net (never; read + draft only).
