# Capstone Readiness Assessment — TeacherMind / Nova

**Track:** Concierge Agents · **Deadline:** 2026-07-06 (15 days)
**v1:** 2026-06-21 (morning) · **v2:** 2026-06-21 (updated after the feature/deploy push)

## Bottom line (v2)

Major jump since v1. The single biggest gap — **Nova could talk but couldn't *do* anything** — is
**closed**: the voice console is now wired to **18 tools** (grades, standards, Canvas, parent comms,
spiral homework, DOK activity, weekly quiz, request log). New feature tools shipped (DOK group
activities, weekly quiz, request logger), and the **Cloud Run deploy path is scaffolded**
(Dockerfile, deploy.sh, runbook). Readiness moved from ~60% to **~75%.**

The remaining risk is **not the product — it's the rubric.** The capstone is judged on demonstrating
**≥3 named course concepts**, and the strongest two of those (**multi-agent ADK** and **MCP**) are
still not built. Everything shipped is excellent Gemini function-calling, which is table stakes, not
the specific concepts the judges check for. Closing that — plus a security fix on the deploy — is the
priority for the next two weeks.

## What changed since v1 (the wins)

- ✅ **Voice console wired to tools** (`agent/voice_tools.py` → `web/server.py` lines 29/76/172).
  Nova now answers *and acts* — the #1 blocker is gone.
- ✅ **DOK group-activity generator** (`group_activities.py`) — DOK 1–3 leveled, with group roles,
  uploaded to Drive. The headline feature exists in v1 form.
- ✅ **Weekly quiz generator** (`weekly_quiz.py`) — 10-question quiz + answer key, Drive upload.
- ✅ **Request logger** (`request_logger.py` → `00_Inbox_from_Karrie/Nova_Request_Log.csv`) — Nova
  logs/recalls what Karrie has been working on (`get_recent_requests`).
- ✅ **Deploy scaffolding** — `Dockerfile`, `deploy.sh`, `docs/runbook_deployment.md` (Secret Manager
  for the key, 3600s timeout, console buttons for Homework / Group Activities).

## Target-deliverable scorecard

| Deliverable | Status | Note |
|---|---|---|
| Talkable Nova that uses tools | ✅ Done | 18 tools wired into the Live console |
| Homework generation | ✅ Done | spiral `.xlsx` → Drive, 13 tests, live-verified |
| DOK assessments / group activities | 🟡 v1 | works, but **Markdown not `.xlsx`**, no verb-cue self-check, no DOK ladder |
| Weekly quiz | ✅ Bonus | not in any spec — nice extra assessment capability |
| Curriculum awareness ("what's next") | 🟡 Partial | request log recalls *past* topics; the **pacing calendar is not built** |
| Anonymous progress tracking | ❌ Not built | mastery store / diagnostics still on paper (specّd, not coded) |
| Online + phone-usable | 🟡 Scaffolded | Dockerfile/deploy/runbook ready; **not yet deployed or phone-tested** |
| **≥3 course concepts** | ⚠ At risk | see below — the real gap |

## The real gap: course concepts (judged ≥3)

| Concept | State | What's needed |
|---|---|---|
| Multi-agent ADK | ❌ | Still single-agent function-calling. Needs the ADK orchestrator (Session 7). |
| MCP server | ❌ | Not started. Needs the Curriculum/Drive MCP (Session 5). |
| Agent Skills | 🟡 | Tools exist but not as `SKILL.md` skills — easy to expose. |
| Security / eval | 🟡 | `/ws` was hardened **but the deploy reopens it** (see risk #1). |
| Spec-Driven Dev | ✅ | Strong, well-documented spec trail in `docs/`. |

You can *credibly* claim **SDD + Agent Skills + Security** with small additions, but the headline
concepts the judges most expect (**multi-agent ADK, MCP**) need real work. Landing **one** of those
two takes you from "defensible" to "strong." Recommend **MCP server (Session 5)** as the highest
leverage — it also unifies the data layer.

## New risks introduced by the push

1. **Security regression on deploy (most important).** `deploy.sh` + the runbook use
   `--allow-unauthenticated` and set **no `CONSOLE_TOKEN`**. The `/ws` socket *spends your API key*;
   deployed as written it is a **public, unauthenticated, key-spending endpoint**. Add the token
   (and keep `--allow-unauthenticated` only because Cloud Run needs it for the browser, with the
   app-level token enforced) **before** any public deploy.
2. **New feature tools have no tests.** `group_activities.py` and `weekly_quiz.py` ship untested,
   unlike the 13-test spiral generator. Add at least canned-response tests.
3. **DOK deviates from the locked spec.** Output is Markdown to a flat `Group Activities` Drive
   folder, not `.xlsx` under `02_Generated/Assessments_DOK/<topic>`, and skips the verb-cue
   self-check + ladder. Fine as a v1, but reconcile with `2026-06-21-dok-builder.md` or update the spec.
4. **Test isolation slipped.** `agent/tools/__init__.py` now eagerly imports the Gemini SDK, so the
   previously offline model/renderer tests require `google-genai` installed to even collect. Keep the
   pure units importable without the SDK.
5. **Curriculum awareness is thinner than it looks.** The request log recalls *past* requests; it
   does not tell Nova what unit comes *next*. The pacing sheet (Session 4) still does that job.

## Updated path to 2026-07-06

1. **Fix the deploy security** (token on `/ws`) — small, do it first; it's a correctness bug, not a feature.
2. **Land one headline concept:** build the **Curriculum/Drive MCP** (Session 5) — unifies data *and*
   checks the MCP box. Stretch: the ADK orchestrator (Session 7) for multi-agent.
3. **Deploy + phone-test** — the scaffolding is ready; prove the mic works over HTTPS and Nova uses
   tools from a phone.
4. **Tests for the new tools**; reconcile DOK output with the spec (or amend the spec to Markdown).
5. **Submission package:** record the demo and explicitly name the ≥3 concepts shown.

**Net:** the product is genuinely close and now actually *does the work*. Spend the next two weeks on
the rubric (concepts + secure deploy + phone proof), not on more features.
