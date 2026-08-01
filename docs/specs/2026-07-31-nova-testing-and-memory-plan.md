# Nova Test & Memory Improvement Plan — 2026-07-31

> **UPDATE (same day) — live testing completed, root causes CONFIRMED.**
> Nova was tested directly (scripted typed-text WebSocket client against the local server,
> same model/prompt/tools as prod) and production Cloud Run logs were read. Results:
>
> 1. **Drive upload is broken everywhere — CONFIRMED root cause of "no homework delivered".**
>    `.nova_drive_token.json` refresh token is dead (`invalid_grant`). It's baked into the
>    Cloud Run image (built 2026-06-23), so every upload fails; the xlsx is generated but
>    stranded on the container's ephemeral disk. Nova even says so: *"I tried to get that
>    saved to Google Drive for you, but it didn't quite work, so I've saved it locally."*
>    The Gmail approval email uses the same token → also broken.
>    **Fix:** re-run OAuth consent (browser) to mint a fresh token AND stop baking tokens
>    into images — service account or Secret Manager + published (non-Testing) OAuth app.
> 2. **Production has NEVER executed a tool call.** Zero `[Orchestrator]` lines in 30 days
>    of Cloud Run logs. Sessions on 7/28–7/29 died with Live API errors: `1008` and
>    `1011 Resource exhausted (check quota)` — the live-preview model's quota killed
>    conversations mid-session. Check quota/billing for the June-23 API key (deploy notes
>    say the disposable judging key was to be revoked 7/7).
> 3. **Windows-only: emoji print crash (`web/server.py:178`)** — `⚙️`/`🚀` prints throw
>    `UnicodeEncodeError` under cp1252 and kill the session at the FIRST tool call. Affects
>    local testing only (Cloud Run is UTF-8). Fix: `PYTHONUTF8=1` or replace prints with
>    logging without emoji.
> 4. **H1 ("(soon)" prompt wording) and H2 (arg friction) largely disproven** for typed
>    text: with the crash fixed, Nova ran the full chain unprompted —
>    `map_assignment_to_standard → get_recent_requests → log_nova_task →
>    generate_spiral_homework → update_task_status` — asking exactly one clarifying
>    question. (Voice behavior may still differ; prompt cleanup is still worthwhile.)
> 5. Memory findings below stand unchanged (log CSV still ephemeral, cache still in-proc).
>
> Repro assets: scripted client at scratchpad `nova_ws_test.py`; generated proof file
> `generated/Friday August 7th spiral (regular).xlsx`.

**Symptoms reported:** Nova (voice console on Cloud Run, used from Karrie's phone) converses
fine but never actually creates homework; she also seems to have no long-term memory.

**Deployed path (confirmed):** `deploy.sh` → Cloud Run `nova-voice-console` running
`web/server.py` (FastAPI + Gemini Live API, model `gemini-3.1-flash-live-preview`), tools from
`agent/voice_tools.py`, system prompt `web/nova_voice_prompt.py`. The ADK orchestrator
(`agent/adk_orchestrator.py`) is NOT what runs on the phone.

---

## Part 1 — Why homework isn't getting created (ranked hypotheses)

### H1 (most likely): The system prompt tells Nova homework is "coming soon"
`web/nova_voice_prompt.py` line 23–25:

> "…drafting parent messages, and **(soon) generating 6th-grade math homework** and
> Depth-of-Knowledge small-group activities."

The `generate_spiral_homework` tool IS registered and declared, but the prompt explicitly says
the capability isn't available yet. A well-behaved model will chat about homework and defer
instead of calling the tool.

### H2: Argument-collection friction stalls the conversation before the tool call
- `generate_spiral_homework` requires **5 args**: `current_topic`, `current_standards`,
  `review_standards`, `due_date`, `school_year`.
- The prompt's Anti-Hallucination Guardrail forbids guessing any of them, and the Request
  Logging Workflow demands `map_assignment_to_standard` + `log_nova_task` first.
- Karrie won't say "review standards 6.NS.B.3" out loud; Nova must interrogate her for codes.
- `MAX_TURNS_PER_SESSION=15` (web/server.py) — a clarifying-question loop can burn the whole
  session before the tool ever fires, then the socket is closed as a "rate limit".

### H3: Google Drive upload fails in the container
`drive_store.py` `_get_creds()` uses an InstalledAppFlow OAuth token:
- `.nova_drive_token.json` is baked into the image at build time (not in `.dockerignore`).
- If the GCP OAuth consent screen is in **Testing** mode, refresh tokens expire after
  **7 days** — the app was deployed for the 2026-07-06 Kaggle deadline, ~3.5 weeks ago.
- On failure inside Cloud Run, `run_local_server()` would hang/throw (no browser); the tool
  returns `drive_error`, the xlsx lands only on the container's ephemeral disk, and Karrie
  gets nothing.

### H4: Live-preview model is weak at multi-step tool chaining
The prompt requires a 3–4 call chain (map → log → generate → update status) in a voice
session; preview live models frequently drop these chains mid-way.

### Test plan (in order — each step produces evidence before any fix)

1. **Read production evidence first**:
   `gcloud run services logs read nova-voice-console --region us-central1 --limit 500`
   The server prints `[Orchestrator] ⚙️/🚀 …` on every tool call. Look for:
   - Zero `generate_spiral_homework` calls → confirms H1/H2 (model never tries).
   - Calls present but followed by errors / `drive_error` → confirms H3.
   - "Rate limit exceeded" disconnects → confirms H2/turn cap.
2. **Local repro**: `python run_console.py`, typed-text turns simulating Karrie
   ("Nova, make this week's homework — we're on dividing fractions, due Friday").
   Watch the console for whether/when the tool fires and what stalls it.
3. **Direct tool test (bypasses the model)**:
   `python -m agent.tools.spiral_homework --topic "Dividing Fractions" --standards 6.NS.A.1 --review 6.NS.B.3 --due 8/8 --year 2025-2026`
   Confirms generator + Drive auth independently. Also verify token freshness locally.
4. **Fix in this order, one at a time, re-testing after each** (per systematic-debugging):
   a. Remove "(soon)" and explicitly list homework generation as a live capability with an
      example invocation phrase.
   b. Soften required args: make `review_standards` optional (auto-select from
      `docs/karrie_profile/05_scope_sequence.md` pacing / recent request log), default
      `school_year` from today's date, accept plain-language due dates.
   c. Raise `MAX_TURNS_PER_SESSION` (e.g. 40) — 15 is too low for a real planning chat.
   d. If H3 confirmed: publish the OAuth app OR switch Drive/Gmail to a **service account**
     (domain-wide files shared to Karrie), store token in Secret Manager, not the image.
5. **Fix stale tests**: `tests/spiral_homework/test_orchestrator.py` asserts
   `res["local_path"].exists()` but the function returns `str` — wrap in `Path(...)`.
6. **End-to-end phone test with Karrie** only after 1–5 pass.

---

## Part 2 — The missing memory layer (confirmed)

Today Nova has **zero durable memory** in production:

| Layer | Current state | Failure mode on Cloud Run |
|---|---|---|
| In-conversation | Gemini Live session context | Dies when the WebSocket closes (every app close / 15-turn cap) |
| `VOICE_SESSION_CACHE` | In-process dict, key `"default"` | Lost at scale-to-zero (`--min-instances 0`); not shared across the 2 instances |
| `Nova_Request_Log.csv` | Written to **container-local disk** (`docs/00_Inbox_from_Karrie/`) | Wiped on every cold start → `get_recent_requests` almost always answers "log is empty" |
| Long-term profile/preferences | None | Nova re-meets Karrie every session |

So the one "memory" tool Nova has (`get_recent_requests`) is effectively non-functional in
the deployed environment — the user-visible effect is exactly "she doesn't learn or retain
anything."

### Recommended memory architecture (tiered, cheapest-first)

**Tier 1 — Make the request log durable (small change, big win)**
Move `request_logger.py` from local CSV to **Firestore** (native on Cloud Run, free tier,
no schema migration — same 6 fields) or a Google Sheet (Drive auth already exists).
This alone restores "what did we work on recently" across sessions and devices.

**Tier 2 — Session-start briefing (episodic memory, read side)**
On each WebSocket connect, build the system prompt dynamically:
`NOVA_VOICE_PROMPT + recent requests (Firestore) + pending approvals + current pacing week
(from scope & sequence)`. Nova opens the conversation already knowing where Karrie left off.

**Tier 3 — Session-end summarization (episodic memory, write side)**
The server already streams both transcripts. On disconnect, run a cheap Gemini Flash call:
"summarize decisions, preferences expressed, and open loops" → append to a `memories`
collection in Firestore. Include these summaries in the Tier-2 briefing (last N, plus any
marked important).

**Tier 4 — Explicit `remember` / profile memory (semantic memory)**
- Add a `save_memory(fact, category)` tool so Karrie can say "Nova, remember I do spiral
  review on Thursdays" and it persists to a small profile document.
- Load the profile document into every session briefing.
- This is the layer that makes her feel like she "learns."

**Tier 5 (later, optional) — Managed memory / retrieval**
If/when migrating to ADK runtime (see `docs/architecture/adk-migration.md`), Google's
**Vertex AI Agent Engine Memory Bank** + ADK `MemoryService` provides managed long-term
memory with retrieval; or add embedding search over past homework/quiz artifacts. Overkill
for a single-teacher app today — Tiers 1–4 cover the observed gap.

### Memory test plan
1. Unit: request logger against Firestore emulator (write, update, read-back ordering).
2. Cross-session: session A "we're starting ratios, quiz Friday" → kill socket → session B
   "what were we doing?" → Nova must answer from the briefing, not apologize.
3. Cold-start: force a new Cloud Run revision / scale-to-zero between A and B (this is the
   case that fails today).
4. Multi-instance: two concurrent sessions must see the same log (fails today with the
   in-proc cache).
5. Profile: "remember X" in session A → verify Nova applies X unprompted in session C.

---

## Suggested execution order
1. Phase A: evidence gathering (log read + local repro) — confirms which homework hypothesis is real.
2. Phase B: homework fixes a→d, one at a time, retest each.
3. Phase C: Tier 1 + Tier 2 memory (durable log + session briefing).
4. Phase D: Tier 3 + Tier 4 (summaries + remember tool).
5. Phase E: end-to-end test with Karrie on her phone; then consider Tier 5.
