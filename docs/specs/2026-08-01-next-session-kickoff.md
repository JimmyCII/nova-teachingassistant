# Next Session Kickoff — Nova Memory Layer (after 2026-08-01)

> **UPDATE (same day, second session): Tiers 1 + 2 are DONE and verified in prod**
> (revision 00016-7dc). Request log lives in Firestore (`nova_request_log`); a
> session-start briefing is injected per WebSocket connect; cold-start recall
> confirmed against a fresh prod revision. Remaining for a future session:
> **Tier 3** (session-end summaries → `memories` collection) and **Tier 4**
> (`save_memory` profile tool) from the 07-31 spec — that's the "Nova, remember
> that I do spiral review on Thursdays" layer. Local dev note: Firestore uses
> ADC (`gcloud auth application-default login`) + `GOOGLE_CLOUD_PROJECT` in `.env`;
> tests force the CSV backend via `tests/conftest.py`.

## Kickoff prompt (paste this to start the session)

> Nova's homework pipeline is fixed and verified in prod (see
> `docs/specs/2026-08-01-next-session-kickoff.md`). This session: implement the
> memory layer from Part 2 of `docs/specs/2026-07-31-nova-testing-and-memory-plan.md` —
> start with Tier 1 (move `agent/tools/request_logger.py` from local CSV to Firestore)
> and Tier 2 (session-start briefing injected into the system prompt on WebSocket
> connect in `web/server.py`). Follow the memory test plan in that spec, especially
> the cold-start and multi-instance cases. Work on a branch, test locally with
> `tests/manual/nova_ws_test.py`, and I'll run `deploy.sh` when we're ready.

## Where things stand (2026-08-01, end of session)

**Working in prod** (Cloud Run `nova-voice-console`, us-central1, rev 00015-mk7):
full voice/text chain — map standard → log task → generate spiral homework →
upload to Google Drive → approval email → update status. Verified end-to-end
against production with `tests/manual/nova_ws_test.py`.

**Fixed this session:** Windows emoji crash (UTF-8 reconfigure in `web/server.py`),
"(soon)" prompt wording, MAX_TURNS 15→40, homework tool now needs only
topic/current standards/due date (review standards auto-picked from request log,
school year defaults from date), stale tests, new API key (Secret Manager
`GOOGLE_API_KEY` v9), durable OAuth (app published to production; token for
`novateacherassistant@gmail.com` served via `NOVA_DRIVE_TOKEN_JSON` secret,
never baked into the image), `mcp<2` pin.

## Next goal: durable memory (the "Nova doesn't learn" half)

From `2026-07-31-nova-testing-and-memory-plan.md` Part 2:

- **Tier 1** — request log → Firestore (same 6 fields; the CSV lives on
  container-local disk today and is wiped at scale-to-zero, so
  `get_recent_requests` and the new review-standard auto-select are amnesiac
  in prod).
- **Tier 2** — session-start briefing: on WS connect, build the system prompt as
  `NOVA_VOICE_PROMPT + recent requests + pending approvals + current pacing week`.
- **Tier 3/4 if time** — session-end summaries; `save_memory` tool + profile doc.
- Test plan: unit (Firestore emulator), cross-session recall, cold-start,
  multi-instance, profile recall — all listed in the 07-31 spec.

## Operational gotchas (learned the hard way)

- **Deploys must be run by Jim** (permission classifier blocks Claude):
  `! cd "C:\Users\jimco\Dev\Kaggle Challenge\Teacher Agent"; bash deploy.sh`
- **Secrets**: push byte-exact via a python temp file, never a PowerShell pipe
  (a pipe corrupted the API key once — v8 disabled, v9 good). New secrets need
  `roles/secretmanager.secretAccessor` for
  `346624345482-compute@developer.gserviceaccount.com`.
- **`mcp` is pinned `<2`** — 2.0.0 removed `mcp.server.fastmcp`.
- Line-buffering fix for `[Orchestrator]` logs is committed but reaches prod on
  the next deploy — after it lands, tool calls are visible in Cloud Run logs.
- OAuth re-mint (if ever needed): delete token file, call `_get_creds()` locally,
  authorize as **novateacherassistant@gmail.com**, then update the
  `NOVA_DRIVE_TOKEN_JSON` secret.
