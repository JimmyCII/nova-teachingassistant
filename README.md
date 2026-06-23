# TeacherMind — AI Concierge Agent for K-8 Mathematics Teachers

**Kaggle Capstone — Concierge Agents track · Submission deadline: July 6, 2026**
**Author:** Jim Cockerham · *5-Day AI Agents: Intensive Vibe Coding Course with Google*

TeacherMind is a conversational AI concierge agent (Google **Gemini** + **ADK**, target deploy
**Cloud Run**) that helps a 6th-grade Arizona math teacher cut administrative burden. It has two
faces today:

1. **Nova Voice Console** (`web/`) — a browser app where the teacher *talks* to **Nova** (her
   assistant persona) over the **Gemini Live API**, with an audio-reactive arc-reactor orb in her
   colors. This is the "meet Nova" experience.
2. **TeacherMind data agent** (`agent/`) — a Gemini function-calling agent that reads a Synergy
   gradebook export, maps work to Arizona Math Standards, flags at-risk students, pulls Canvas
   curriculum, and drafts School-Net parent messages — always teacher-in-the-loop.

**Nova** is a persona built *in the spirit of* a real teacher, Karrie (not a clone). The persona
research lives in `docs/karrie_profile/` (local-only — see PII note).

> **Canonical spec:** [`CAPSTONE_SPEC.md`](./CAPSTONE_SPEC.md) ·
> **Scope / non-goals / acceptance:** [`docs/requirements.md`](./docs/requirements.md) ·
> **Primary-role spec:** [`docs/superpowers/specs/2026-06-20-nova-teaching-assistant-design.md`](./docs/superpowers/specs/2026-06-20-nova-teaching-assistant-design.md)

---

## Status

| | |
|---|---|
| **Nova voice console** | ✅ `web/` — talk to Nova in the browser (Gemini Live API); arc-reactor orb, hands-free, mobile-first, speaker-aware, security-hardened. `python run_console.py` |
| **TeacherMind data agent** | ✅ `agent/` — Gemini function-calling, 12 tools (grades/standards/Canvas/parent-comms), CLI |
| **Persona** | ✅ `docs/karrie_profile/` (local-only) — Nova persona + system prompt; voice persona in `web/nova_voice_prompt.py` |
| **Homework knowledge base** | ✅ `docs/karrie_profile/homework/` (local) — spiral style guide + exemplars + templates from 54 weekly files |
| **Spiral homework generator** | ✅ **built & live-verified** (`feat/spiral-homework`) — Gemini spiral mix → editable `.xlsx` (Karrie's 4-col format) → Nova's Drive `Homework/<year>/Drafts`, shared with Karrie. 13 tests. `python -m agent.tools.spiral_homework …` |
| **Key gaps** | ⚠ Nova not yet wired into the `agent/` tools (console talks, but can't use grade/homework tools yet); not deployed to Cloud; homework/DOK builders not built |
| **Next session** | [`prompts/session-2-kickoff.md`](./prompts/session-2-kickoff.md) |

## Quick start

**Talk to Nova (voice console):**
```bash
pip install -r requirements.txt
# .env must hold GOOGLE_API_KEY (+ GOOGLE_CLOUD_PROJECT). See .env.example.
python run_console.py          # → http://localhost:8000 — press Talk, allow the mic, say hi
```

**TeacherMind data agent (CLI):**
```bash
python run.py                  # or: python -m agent.agent
# try: "Load sample_data/synergy_export_sample.csv — who's struggling in Period 2?"
```

**ADK Multi-Agent Orchestrator (Smoke Test):**
Verify that the formal Google ADK framework correctly routes complex tasks to specialized Sub-Agents (Homework, DOK, Quizzes).
```bash
python test_adk_routing.py     # Live Gemini routing test
```

---

## Repository layout

```
.
├── CAPSTONE_SPEC.md          # Canonical project spec (TeacherMind)
├── README.md / AGENTS.md / CLAUDE.md / CODEX_BOOTSTRAP.md / DEPENDENCIES.md
├── run.py                    # CLI entry (data agent)        run_console.py  # voice console entry
├── requirements.txt
├── web/                      # NOVA VOICE CONSOLE
│   ├── server.py             #   FastAPI + WebSocket bridge to the Gemini Live API
│   ├── nova_voice_prompt.py  #   Nova's spoken persona (PII-free)
│   └── static/               #   index.html · styles.css · app.js  (arc-reactor orb console)
├── agent/                    # TEACHERMIND DATA AGENT (ADK-style package; no src/)
│   ├── agent.py              #   agentic loop + Gemini tool wiring + SYSTEM_PROMPT
│   ├── tools/                #   grade_tools, standards_mapper, canvas_tools, communication_drafter
│   └── data/                 #   az_math_6_standards.json, standard_keywords.json
├── sample_data/              # Synthetic Synergy CSV (no real PII)
├── tests/                    # pytest (test_grade_tools.py)
├── agents/{prompts,logs}/    # multi-agent role prompts; routing + decision logs
├── prompts/                  # session prompts (session-1 record, session-2 kickoff)
└── docs/
    ├── requirements.md · ideas.md · research-voice-options.md
    ├── superpowers/specs/    # design specs
    └── karrie_profile/       # ⚠ LOCAL-ONLY persona research (gitignored — see below)
```

---

## Data & PII handling (read before committing anything)

This project was built by analyzing a real teacher's private files. **FERPA-sensitive material must
never be committed.** Gitignored / local-only:

- `docs/karrie_profile/` — analyst profiles, Nova persona, cleanup notes, legacy extracts,
  `file_inventory_raw.csv`. Several files reference **real student-name filenames** and IEP/SPED/SEI paths.
- `docs/karrie_profile.md` (photo persona guide) · `docs/karrie_exploration_prompt.md` (mission prompt).

All committed sample/test data is **synthetic**. No real student PII ever passes through the voice
console (Nova's prompt forbids it). Before any persona research can be committed it must be
PII-scrubbed.

## Security (voice console)

Localhost-only by default. The `/ws` socket spends the API key, so it enforces a same-origin
**Origin check** (anti-CSWSH) and, when exposed beyond localhost, a constant-time **token** (set
`CONSOLE_TOKEN`, open with `#token=…`). `/health` does not advertise the key. See `web/README.md`.

## Tech stack

Python 3.11+ · `google-genai` (Gemini, incl. Live API) · `google-adk` · `fastapi` + `uvicorn`
(console) · `canvasapi` · `pandas` · `rich` · `python-dotenv`. Target deploy: Google Cloud Run.

## License

MIT — see [`LICENSE`](./LICENSE).
