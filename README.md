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

| Component | Status |
|---|---|
| **Nova voice console** | ✅ `web/` — Talk to Nova in the browser (Gemini Live API); hands-free, mobile-first, deployed to **Cloud Run**. |
| **TeacherMind data agent** | ✅ `agent/` — Gemini function-calling, 18 tools wired directly into the Voice Console. |
| **Pedagogy Critic** | ✅ `agent/` — Evaluates generated content against AZ Math Standards and Webb DOK. |
| **MCP Servers** | ✅ `mcp_servers/` — Curriculum MCP (Standards/DOK) & Comms MCP (Drive watcher/Email loop) running. |
| **Content Generators** | ✅ **built & live-verified** — Generates spiral homework `.xlsx`, DOK activities, and 10-Q Quizzes, saving to Drive. |
| **ADK Smoke Test** | ✅ `tests/test_adk_routing.py` — Verifies formal Google ADK orchestration capabilities. |

## Quick start

### 1. Local Voice Console
```bash
pip install -r requirements.txt
```
Create a `.env` file containing the following:
```env
GOOGLE_API_KEY="your_api_key"
CONSOLE_TOKEN="your_secure_32_byte_token"
KARRIE_EMAIL="target_teacher@email.com"
ADMIN_EMAIL="admin_alert@email.com"
SENDER_EMAIL="agent_sender@email.com"
```
Run the console locally:
```bash
python run_console.py  # → http://localhost:8000
```

### 2. Cloud Run Deployment
The live demo is actively hosted on Google Cloud Run. To deploy your own instance, run the included deploy script (which configures the required scaling caps and pulls secrets from Google Secret Manager):
```bash
./deploy.sh
```
*(See `docs/runbook_deployment.md` for full GCP setup instructions).*

### 3. ADK Multi-Agent Orchestrator (Smoke Test)
Verify that the formal Google ADK framework correctly routes complex tasks to specialized Sub-Agents (Homework, DOK, Quizzes).
```bash
python tests/test_adk_routing.py
```

---

## Repository layout

```text
.
├── CAPSTONE_SPEC.md          # Canonical project spec
├── README.md                 # Project Overview & Quick Start
├── deploy.sh                 # Cloud Run deployment script
├── web/                      # NOVA VOICE CONSOLE (FastAPI + WebSocket)
├── agent/                    # TEACHERMIND DATA AGENTS (Tools & Sub-Agents)
├── mcp_servers/              # FastMCP Servers (Curriculum & Comms)
├── sample_data/              # Synthetic Synergy CSV (no real PII)
├── tests/                    # pytest & ADK smoke tests
└── docs/
    ├── architecture/         # Architectural decisions (ADK vs Voice)
    ├── launch/               # Kaggle Writeup & Judging Safety Specs
    ├── superpowers/specs/    # Design specs
    └── karrie_profile/       # ⚠ LOCAL-ONLY persona research
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
