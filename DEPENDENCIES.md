# Dependencies

Every third-party dependency, its purpose and license. **Permissive licenses only
(MIT / BSD / Apache-2.0).** No new dependency without surfacing the tradeoff and getting a yes
(Project-Playbook §5). Pinned in `requirements.txt`.

## Runtime (from `requirements.txt`)

| Package | Purpose | License |
|---------|---------|---------|
| `google-genai` (>=1.0.0) | Gemini model access + function calling | Apache-2.0 |
| `google-adk` (>=0.3.0) | Agent Development Kit (agent/tools framework, Cloud Run target) | Apache-2.0 |
| `canvasapi` (>=3.3.0) | Canvas LMS REST client | MIT |
| `pandas` (>=2.2.0) | Synergy CSV normalization / grade analysis | BSD-3 |
| `python-dotenv` (>=1.0.0) | Load `GOOGLE_API_KEY` etc. from `.env` | BSD-3 |
| `pydantic` (>=2.7.0) | Data models / validation | MIT |
| `httpx` (>=0.27.0) | HTTP client | BSD-3 |
| `rich` (>=13.7.0) | Terminal UI for the interactive agent loop | MIT |
| `fastapi` (>=0.110.0) | Web server + WebSocket for the Nova voice console (`web/`) | MIT |
| `uvicorn[standard]` (>=0.29.0) | ASGI server (+ websockets) for the console | BSD-3 |
| `openpyxl` (>=3.1.0) | Read/write Karrie's spiral homework .xlsx | MIT |
| `google-api-python-client` (>=2.130) | Google Drive upload | Apache-2.0 |
| `google-auth-oauthlib` (>=1.2) | Drive OAuth (drive.file) | Apache-2.0 |
| `mcp` (>=1.2.0) | Model Context Protocol SDK | MIT |
| `python-docx` (>=1.1.0) | Document generation | MIT |

## Dev

| Package | Purpose | License |
|---------|---------|---------|
| `pytest` | Tests (`tests/test_grade_tools.py`) | MIT |
| _TBD_ | linter / formatter / type-checker (e.g. ruff, mypy) — add when standardized | MIT/Apache |

> All current dependencies use permissive licenses. Update this table whenever `requirements.txt`
> changes.