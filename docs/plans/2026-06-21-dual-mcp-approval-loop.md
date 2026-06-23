# Implementation Plan — Dual MCP Servers + the Approval Loop

> **Execute in Antigravity**, phase by phase. Test-first where noted. Capstone due **2026-07-06**.
> **Specs:** `2026-06-21-drive-curriculum-mcp.md` · `2026-06-21-comms-approval-mcp.md` (new, §Phase 2)
> · `2026-06-21-multi-agent-content-pipeline.md`. Operate per `AGENTS.md`.

**Goal:** prove MCP in the running product (consume the Curriculum server), add a second **Comms/
Approval** MCP server, wire the human-in-the-loop approval loop, and ship a **secure** deploy.

**Concepts this lands (claim these deliberately):** **MCP** (two servers, actually consumed) +
**human-in-the-loop** + **agentic loop** + **SDD** + **secure deploy**. NOTE: this plan does *not*
build the ADK multi-agent orchestrator — that's a separate track; don't assume it's checked off.

---

## Phase 0 — Prerequisites (REQUIRED before Phase 1; Phase 1 fails without these)

**Why:** the folder `mcp/` shadows the pip `mcp` package, so `from mcp.server.fastmcp import FastMCP`
and the new `import mcp` client both break depending on cwd. And the dependency isn't registered.

- [ ] **Rename the server package** so it can't shadow the SDK:
  ```bash
  git mv mcp mcp_servers
  touch mcp_servers/__init__.py mcp_servers/curriculum_server/__init__.py
  ```
  (If the git index is locked/broken, fix git first: remove a stale `.git/index.lock`, confirm
  `git status` is clean-ish, then redo. Commit from your Windows shell where git is healthy.)
- [ ] **Register the dependency** — add to `requirements.txt`:
  ```
  mcp>=1.2.0          # Model Context Protocol SDK (server FastMCP + client)
  ```
  and a row in `DEPENDENCIES.md` (License: MIT). Also add `python-docx>=1.1.0` (already imported by
  `weekly_quiz.py`, still unregistered).
- [ ] **Install + smoke the server** under its new name:
  ```bash
  pip install -r requirements.txt
  python -m mcp_servers.curriculum_server.server   # should start on stdio without import errors
  ```
- [ ] **Commit:** `chore(mcp): rename to mcp_servers (un-shadow SDK) + register mcp/python-docx deps`

---

## Phase 1 — Consume the Curriculum MCP (the guaranteed MCP win)

Replace the critic's direct disk read of the standards with a native MCP `read_resource` call.
Fold in the earlier critic fixes while we're here (text model, injectable provider, `target_dok`).

**Files:** `agent/tools/mcp_client.py` (new) · `agent/tools/pedagogy_critic.py` (edit) ·
`tests/test_pedagogy_critic.py` (new)

- [ ] **Step 1 — MCP client helper** (`agent/tools/mcp_client.py`): a *sync* wrapper that spawns the
  Curriculum server over stdio and reads a resource. Bridges async MCP into our sync tools.
  ```python
  import asyncio
  from mcp import ClientSession, StdioServerParameters
  from mcp.client.stdio import stdio_client

  _CURRICULUM = StdioServerParameters(
      command="python", args=["-m", "mcp_servers.curriculum_server.server"])

  async def _read(uri: str) -> str:
      async with stdio_client(_CURRICULUM) as (r, w):
          async with ClientSession(r, w) as s:
              await s.initialize()
              res = await s.read_resource(uri)
              return res.contents[0].text  # FastMCP resource returns text contents

  def read_resource(uri: str) -> str:
      """Sync: read an MCP resource (e.g. 'standards://az-math-6'). Raises on failure."""
      return asyncio.run(_read(uri))
  ```
- [ ] **Step 2 — refactor the critic** to take an injectable standards provider (testable) and use a
  real text model, not the Live model:
  ```python
  import os
  _CRITIC_MODEL = os.getenv("CRITIC_MODEL", "gemini-2.5-flash")   # NOT NOVA_LIVE_MODEL

  def _standards_via_mcp() -> str:
      from agent.tools.mcp_client import read_resource
      return read_resource("standards://az-math-6")

  def review_and_revise(draft_text, content_type="quiz", target_dok=2,
                        _standards_provider=_standards_via_mcp) -> dict:
      try:
          standards = _standards_provider()
          source = "mcp"
      except Exception:
          # resilient fallback so the product never breaks — but the DEMO path must hit MCP
          from pathlib import Path
          p = Path(__file__).resolve().parents[2] / "agent/data/az_math_6_standards.json"
          standards = p.read_text(encoding="utf-8") if p.exists() else "{}"
          source = "disk-fallback"
      # ... build system_instruction with target_dok + the *relevant* standards (not a raw slice) ...
      # call Gemini(_CRITIC_MODEL) ...
      return {"verdict": "revised", "issues": [...], "revised_text": revised, "standards_source": source}
  ```
  Improvements folded in: **structured return** (`verdict`/`issues`/`revised_text` — visible, loggable),
  **`target_dok`** so the same critic serves DOK 1–3 activities, and **no truncated-JSON blob**.
- [ ] **Step 3 — update the quiz caller** (`weekly_quiz.py`) to use `result["revised_text"]` and log
  `result["issues"]` (and assert `standards_source == "mcp"` in the live smoke).
- [ ] **Step 4 — test** (`tests/test_pedagogy_critic.py`, no network): inject a fake provider +
  fake Gemini call; assert the prompt embeds the provided standards and the result is structured;
  assert disk-fallback triggers when the provider raises.
- [ ] **Step 5 — live smoke:** generate a quiz; confirm logs show `standards_source=mcp` (real
  consumption, not fallback).
- [ ] **Commit:** `feat(mcp): critic consumes Curriculum MCP standards resource (+ target_dok, text model, structured verdict)`

---

## Phase 2 — Build the Comms/Approval MCP server

New server `mcp_servers/comms_server/server.py`. **Gmail API (send scope), not smtplib.**

**Files:** `mcp_servers/comms_server/{__init__.py,server.py}` · extend `drive_store.py`
(scope + parents helper) · `tests/test_comms_server.py`

- [ ] **Step 1 — add the Gmail send scope** to the shared OAuth. In `drive_store.py`:
  ```python
  SCOPES = ["https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/gmail.send"]
  ```
  **Note:** adding a scope invalidates the cached token — delete `.nova_drive_token.json` and
  re-consent once as Nova's account. (Least privilege: send-only; no inbox read.)
- [ ] **Step 2 — Drive approval helper** in `drive_store.py` (works under `drive.file` because the
  app created the file):
  ```python
  def is_in_approved(self, file_id: str) -> bool:
      meta = self._svc.files().get(fileId=file_id, fields="parents").execute()
      for pid in meta.get("parents", []):
          name = self._svc.files().get(fileId=pid, fields="name").execute().get("name")
          if name == "03_Approved":
              return True
      return False
  ```
- [ ] **Step 3 — the server + two tools:**
  ```python
  from mcp.server.fastmcp import FastMCP
  mcp = FastMCP("Comms Server")

  @mcp.tool()
  def send_draft_for_approval(to_email: str, drive_link: str, doc_name: str, topic: str) -> str:
      """Email Karrie a link to review/approve a draft. Curriculum content only — never student PII."""
      # build a MIME message; send via Gmail API (build('gmail','v1')...users().messages().send)
      # PRINT/MOCK fallback if creds/secret missing -> return "MOCK: would email <to> <link>"

  @mcp.tool()
  def check_drive_approvals(file_id: str) -> dict:
      """PULL: has Karrie moved this file into 03_Approved? Returns {approved: bool}."""
      from agent.tools.spiral_homework.drive_store import GoogleDriveClient
      return {"approved": GoogleDriveClient().is_in_approved(file_id)}

  if __name__ == "__main__":
      mcp.run(transport="stdio")
  ```
  Ensure `03_Approved` exists under the root and is shared with Karrie (reuse the ensure/share helpers).
- [ ] **Step 4 — tests** (mock Gmail + a fake Drive client): `send_*` returns success/mock without
  network; `check_drive_approvals` returns `approved=True` when a parent is `03_Approved`, else False.
- [ ] **Commit:** `feat(mcp): comms/approval server — gmail.send + drive 03_Approved check`

---

## Phase 3 — Wire the agentic approval loop

- [ ] **Step 1 — statuses in `request_logger`:** allow `Open → Pending Approval → Approved`.
- [ ] **Step 2 — on generate** (quiz first, then DOK/homework): after `save_draft` + send, call
  `log_nova_task(topic, standard, status="Pending Approval")`; keep the returned `file_id` alongside
  the `Task_ID` in the log (add a `File_ID` column) so approvals can be matched later.
- [ ] **Step 3 — a PULL check flow** Nova runs on demand (a voice tool / console "Check approvals"
  button / the weekly digest — **not** a long-running waiter; Cloud Run is stateless): iterate
  `Pending Approval` rows → `check_drive_approvals(file_id)` → on `approved`,
  `update_task_status(task_id, "Approved")`. Expose as voice tool `check_pending_approvals()`.
- [ ] **Step 4 — test:** fake comms + fake log → a pending task whose file is "in 03_Approved" flips
  to Approved; one that isn't stays pending.
- [ ] **Optional:** a `mcp__scheduled-tasks` daily poll that runs the pull check and emails a digest.
- [ ] **Commit:** `feat(loop): pending-approval logging + pull-based drive approval -> request log`

---

## Phase 4 — Secure the deploy (do NOT leave for last; ~10 lines)

The `/ws` socket spends the API key; today's `deploy.sh` is `--allow-unauthenticated` with **no
token**. Keep `--allow-unauthenticated` (Cloud Run needs it so the browser can load the page) but
**enforce the app-level `CONSOLE_TOKEN`** the server already supports.

- [ ] **Step 1 — create the secret:** `echo -n "<long-random>" | gcloud secrets create CONSOLE_TOKEN --data-file=-`
- [ ] **Step 2 — `deploy.sh` + runbook:** add `CONSOLE_TOKEN=CONSOLE_TOKEN:latest` to `--set-secrets`.
- [ ] **Step 3 — verify** the server rejects `/ws` without the token and accepts `…/#token=<value>`.
- [ ] **Step 4 — phone test:** open `https://…run.app/#token=…`; mic works over HTTPS; Nova talks
  **and** uses tools; a generated draft emails the approval link.
- [ ] **Commit:** `fix(deploy): enforce CONSOLE_TOKEN on the deployed console (close open /ws)`

---

## Recommended order
**Phase 0 → Phase 1 → Phase 4 (early/parallel — it's small and it's a safety bug) → Phase 2 → Phase 3.**
Land Phase 1 for a guaranteed MCP integration on the board; do the deploy-security fix as soon as it's
convenient so an insecure endpoint is never the thing left at the buzzer.

## Definition of done
- Critic reads standards via MCP in the live path (`standards_source=mcp`).
- Comms MCP sends an approval email (or clean mock) and detects `03_Approved` moves.
- Request log walks `Pending Approval → Approved` from a real Drive move.
- Deployed console requires a token; phone test passes end-to-end.
- A test lands in each phase; `mcp`/`python-docx` registered; no student PII on any surface.
