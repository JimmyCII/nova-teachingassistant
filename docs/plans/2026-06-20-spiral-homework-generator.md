# Spiral Homework Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable tool that generates Karrie's weekly Spiral Review homework as an editable `.xlsx` in her format and saves it to Nova's Google Drive.

**Architecture:** Split "thinking" from "drawing." Gemini writes the week's problems (the spiral mix) into a validated `WeekSpec`; a deterministic openpyxl renderer draws the 4-column Mon–Thu grid `.xlsx`; a thin Drive wrapper uploads it to `Nova Teaching Assistant / Homework / <year> / Drafts` (shared with Karrie). A CLI orchestrates generate → render → upload, with a local fallback if Drive fails.

**Tech Stack:** Python 3.11, pydantic, openpyxl, google-genai (Gemini), google-api-python-client + google-auth-oauthlib (Drive), pytest.

**Spec:** `docs/superpowers/specs/2026-06-20-spiral-homework-generator-design.md`
**Knowledge base (local):** `docs/karrie_profile/homework/`

---

## File Structure

```
agent/tools/spiral_homework/
├── __init__.py          # exports generate_spiral_homework
├── models.py            # Box, WeekSpec (pydantic) + spiral-mix validation
├── renderer.py          # render_xlsx(week, out_path) -> Path   (openpyxl, pure/offline)
├── generator.py         # generate_week_spec(...) -> WeekSpec    (Gemini, injectable call)
├── drive_store.py       # DriveClient protocol, Fake/Google impls, upload_homework()
└── __main__.py          # generate_spiral_homework() + argparse CLI
tests/spiral_homework/
├── __init__.py
├── test_models.py
├── test_renderer.py
├── test_generator.py
├── test_drive_store.py
└── test_orchestrator.py
```

Each file has one responsibility; the renderer and models are pure (no network) and carry most tests.

---

## Task 0: Dependencies, package scaffold, gitignore

**Files:**
- Modify: `requirements.txt`
- Modify: `.gitignore`
- Create: `agent/tools/spiral_homework/__init__.py`
- Create: `tests/spiral_homework/__init__.py`

- [ ] **Step 1: Add dependencies** to `requirements.txt` (append):

```
# Spiral homework generator
openpyxl>=3.1.0
google-api-python-client>=2.130.0
google-auth-oauthlib>=1.2.0
```

- [ ] **Step 2: Install them**

Run: `pip install -q openpyxl google-api-python-client google-auth-oauthlib`
Expected: installs without error (openpyxl already present from analysis).

- [ ] **Step 3: Gitignore secrets + output** — append to `.gitignore`:

```
# Spiral homework generator — local secrets & output
client_secret.json
.nova_drive_token.json
/generated/
```

- [ ] **Step 4: Create empty package files**

`agent/tools/spiral_homework/__init__.py`:
```python
"""Spiral Review homework generator (Gemini -> WeekSpec -> .xlsx -> Drive)."""
from .__main__ import generate_spiral_homework  # noqa: F401
```
`tests/spiral_homework/__init__.py`: (empty file)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore agent/tools/spiral_homework/__init__.py tests/spiral_homework/__init__.py
git commit -m "chore(spiral): deps + package scaffold + gitignore secrets"
```
*(Note: `__init__.py` imports `__main__` which doesn't exist yet — Step 4's import will fail until Task 5. Temporarily make `__init__.py` just the docstring now; add the import in Task 5.)*

---

## Task 1: Data model (`WeekSpec`, `Box`)

**Files:**
- Create: `agent/tools/spiral_homework/models.py`
- Test: `tests/spiral_homework/test_models.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/spiral_homework/test_models.py
import pytest
from pydantic import ValidationError
from agent.tools.spiral_homework.models import Box, WeekSpec

def _box(day="Monday", type="computation", role="current", text="2 + 2 ="):
    return Box(day=day, type=type, role=role, text=text)

def test_valid_weekspec_with_spiral_mix():
    week = WeekSpec(due_date="9/12", track="regular", boxes=[
        _box(role="current", text="1 5/6 × 4 1/2"),
        _box(role="review", type="word_problem", text="A turtle swims 7.5 km in 3 hours..."),
        Box(day="Tuesday", type="brain_break", role="current", text=""),
    ])
    assert week.due_date == "9/12"
    assert len(week.boxes) == 3

def test_spiral_mix_requires_current_and_review():
    with pytest.raises(ValidationError):
        WeekSpec(due_date="9/12", boxes=[_box(role="current"), _box(role="current")])

def test_rejects_unknown_type():
    with pytest.raises(ValidationError):
        Box(day="Monday", type="essay", role="current", text="x")

def test_brain_break_and_figure_excluded_from_mix_rule():
    # only a brain_break + one current computation -> still needs a review -> should fail
    with pytest.raises(ValidationError):
        WeekSpec(due_date="9/12", boxes=[
            _box(role="current"),
            Box(day="Tuesday", type="brain_break", role="current", text=""),
        ])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/spiral_homework/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: ...models`.

- [ ] **Step 3: Implement `models.py`**

```python
# agent/tools/spiral_homework/models.py
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

Day = Literal["Monday", "Tuesday", "Wednesday", "Thursday"]
BoxType = Literal["computation", "word_problem", "brain_break", "figure_placeholder"]
Role = Literal["current", "review"]
Track = Literal["regular", "accelerated"]

_MATH_TYPES = {"computation", "word_problem"}

class Box(BaseModel):
    day: Day
    type: BoxType
    role: Role = "current"
    text: str = ""
    standard_code: Optional[str] = None
    figure_note: Optional[str] = None

class WeekSpec(BaseModel):
    due_date: str
    track: Track = "regular"
    boxes: list[Box] = Field(min_length=1, max_length=24)

    @field_validator("boxes")
    @classmethod
    def _spiral_mix(cls, boxes: list[Box]) -> list[Box]:
        roles = {b.role for b in boxes if b.type in _MATH_TYPES}
        if not ({"current", "review"} <= roles):
            raise ValueError("spiral mix requires at least one 'current' and one 'review' math box")
        return boxes
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/spiral_homework/test_models.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/tools/spiral_homework/models.py tests/spiral_homework/test_models.py
git commit -m "feat(spiral): WeekSpec/Box model with spiral-mix validation"
```

---

## Task 2: Renderer (`render_xlsx`)

**Files:**
- Create: `agent/tools/spiral_homework/renderer.py`
- Test: `tests/spiral_homework/test_renderer.py`

- [ ] **Step 1: Write the failing test** (renders, then reads the `.xlsx` back)

```python
# tests/spiral_homework/test_renderer.py
from openpyxl import load_workbook
from agent.tools.spiral_homework.models import Box, WeekSpec
from agent.tools.spiral_homework.renderer import render_xlsx

def _week():
    return WeekSpec(due_date="9/12", track="regular", boxes=[
        Box(day="Monday", type="computation", role="current", text="1 5/6 × 4 1/2"),
        Box(day="Monday", type="computation", role="review", text="246.75 ÷ 2.5 ="),
        Box(day="Tuesday", type="word_problem", role="review",
            text="A turtle swims 7.5 km in 3 hours. Unit rate?"),
        Box(day="Wednesday", type="brain_break", role="current", text=""),
        Box(day="Thursday", type="figure_placeholder", role="current",
            text="Plot the points.", figure_note="coordinate plane"),
    ])

def test_render_writes_xlsx_with_header_and_grid(tmp_path):
    out = render_xlsx(_week(), tmp_path / "wk.xlsx")
    assert out.exists()
    ws = load_workbook(out).active
    assert "Spiral Review Homework" in str(ws["B1"].value)
    assert "9/12" in str(ws["D1"].value)
    assert [ws.cell(row=2, column=c).value for c in range(1, 5)] == \
        ["Monday", "Tuesday", "Wednesday", "Thursday"]
    # Monday column (col 1) has the two computation problems stacked
    col1 = [ws.cell(row=r, column=1).value for r in range(3, 6)]
    assert any("1 5/6" in str(v) for v in col1)
    assert any("246.75" in str(v) for v in col1)
    # brain break label rendered
    allvals = [c.value for row in ws.iter_rows() for c in row if c.value]
    assert any("Brain Break" in str(v) for v in allvals)
    # figure placeholder note rendered
    assert any("coordinate plane" in str(v) for v in allvals)

def test_render_marks_borders(tmp_path):
    out = render_xlsx(_week(), tmp_path / "wk.xlsx")
    ws = load_workbook(out).active
    assert ws.cell(row=3, column=1).border.left.style == "thin"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/spiral_homework/test_renderer.py -v`
Expected: FAIL with `ModuleNotFoundError: ...renderer`.

- [ ] **Step 3: Implement `renderer.py`**

```python
# agent/tools/spiral_homework/renderer.py
from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from .models import Box, WeekSpec

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday"]

def _box_text(box: Box) -> str:
    if box.type == "brain_break":
        return "Brain Break!"
    text = box.text or ""
    if box.type == "figure_placeholder" or box.figure_note:
        text = f"{text}\n[figure: {box.figure_note or 'see teacher'}]".strip()
    return text

def render_xlsx(week: WeekSpec, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Spiral Review"
    bold = Font(bold=True)
    center = Alignment(horizontal="center")

    ws["A1"] = "Name ____________"
    ws["B1"] = "Spiral Review Homework"; ws["B1"].alignment = center
    ws["D1"] = f"Due {week.due_date}"; ws["D1"].alignment = Alignment(horizontal="right")

    for i, day in enumerate(DAYS):
        c = ws.cell(row=2, column=i + 1, value=day)
        c.font = bold; c.alignment = center

    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    by_day = {d: [b for b in week.boxes if b.day == d] for d in DAYS}
    max_rows = max((len(v) for v in by_day.values()), default=0)

    for col_i, day in enumerate(DAYS):
        for row_i, box in enumerate(by_day[day]):
            cell = ws.cell(row=3 + row_i, column=col_i + 1, value=_box_text(box))
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = border

    for col_i in range(1, 5):
        ws.column_dimensions[get_column_letter(col_i)].width = 26
    for r in range(3, 3 + max_rows):
        ws.row_dimensions[r].height = 90

    wb.save(out_path)
    return out_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/spiral_homework/test_renderer.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/tools/spiral_homework/renderer.py tests/spiral_homework/test_renderer.py
git commit -m "feat(spiral): openpyxl renderer for the 4-col Mon-Thu grid"
```

---

## Task 3: Generator (`generate_week_spec`, Gemini with injectable call)

**Files:**
- Create: `agent/tools/spiral_homework/generator.py`
- Test: `tests/spiral_homework/test_generator.py`

- [ ] **Step 1: Write the failing tests** (inject a fake `_call` so no network)

```python
# tests/spiral_homework/test_generator.py
import json
import pytest
from agent.tools.spiral_homework.generator import generate_week_spec
from agent.tools.spiral_homework.models import WeekSpec

_GOOD = {
    "due_date": "9/12", "track": "regular",
    "boxes": [
        {"day": "Monday", "type": "computation", "role": "current", "text": "1 5/6 × 4 1/2"},
        {"day": "Monday", "type": "computation", "role": "review", "text": "246.75 ÷ 2.5 ="},
        {"day": "Tuesday", "type": "word_problem", "role": "review",
         "text": "A turtle swims 7.5 km in 3 hours. Unit rate?"},
        {"day": "Wednesday", "type": "brain_break", "role": "current", "text": ""},
    ],
}

def test_generates_valid_weekspec_from_model_json():
    calls = []
    def fake_call(prompt, model):
        calls.append((prompt, model))
        return "```json\n" + json.dumps(_GOOD) + "\n```"
    week = generate_week_spec("Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12",
                              track="regular", _call=fake_call)
    assert isinstance(week, WeekSpec)
    assert week.due_date == "9/12"
    assert "Fractions" in calls[0][0]  # topic made it into the prompt

def test_retries_once_then_raises_on_garbage():
    attempts = {"n": 0}
    def fake_call(prompt, model):
        attempts["n"] += 1
        return "not json at all"
    with pytest.raises(ValueError):
        generate_week_spec("Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12", _call=fake_call)
    assert attempts["n"] == 2  # one retry
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/spiral_homework/test_generator.py -v`
Expected: FAIL with `ModuleNotFoundError: ...generator`.

- [ ] **Step 3: Implement `generator.py`**

```python
# agent/tools/spiral_homework/generator.py
from __future__ import annotations
import json
import os
import re
from typing import Callable
from .models import WeekSpec

_MODEL = os.getenv("HOMEWORK_MODEL", "gemini-2.0-flash")

_PROMPT = """You create ONE week of a 6th-grade Arizona math teacher's "Spiral Review" homework.
Format: 4 columns (Monday–Thursday), about 14–16 boxes total (~4 per day). Each box is one item.

Spiral mix: about half the math boxes are the CURRENT topic and about half are REVIEW of earlier
standards. Include 2–4 "word_problem" boxes with real-world contexts and rotating FICTIONAL names
(never a real student). Include exactly ONE "brain_break" box (text "" ). For a problem that needs a
picture, use type "figure_placeholder" with a short "figure_note" (e.g. "number line 0-10").
Use plain editable text math (e.g. "1 5/6 × 4 1/2", "z ÷ 6 = 1.5"). NO student data.

current_topic: {topic}
current_standards: {current}
review_standards: {review}
due_date (header label): {due}
track: {track}   (if "accelerated": drop basic computation warm-ups, add more conceptual/algebra)

Return ONLY JSON (no prose) with this exact shape:
{{"due_date": "{due}", "track": "{track}", "boxes": [
  {{"day": "Monday|Tuesday|Wednesday|Thursday",
    "type": "computation|word_problem|brain_break|figure_placeholder",
    "role": "current|review", "text": "...", "standard_code": "6.XX.X.X" or null,
    "figure_note": "..." or null}} ]}}"""

def _call_gemini(prompt: str, model: str) -> str:
    from google import genai  # imported lazily so tests need no network/SDK call
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return client.models.generate_content(model=model, contents=prompt).text

def _extract_json(raw: str) -> dict | None:
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def generate_week_spec(current_topic: str, current_standards: list[str],
                       review_standards: list[str], due_date: str, track: str = "regular",
                       model: str = _MODEL,
                       _call: Callable[[str, str], str] = _call_gemini) -> WeekSpec:
    prompt = _PROMPT.format(topic=current_topic, current=", ".join(current_standards),
                            review=", ".join(review_standards), due=due_date, track=track)
    last_err = "no response"
    for _ in range(2):
        data = _extract_json(_call(prompt, model))
        if data is not None:
            try:
                return WeekSpec.model_validate(data)
            except Exception as e:  # validation failure -> retry
                last_err = str(e)
    raise ValueError(f"Gemini did not return a valid WeekSpec after retry: {last_err}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/spiral_homework/test_generator.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add agent/tools/spiral_homework/generator.py tests/spiral_homework/test_generator.py
git commit -m "feat(spiral): Gemini week-spec generator (injectable call, retry+validate)"
```

---

## Task 4: Drive store (protocol + fake + google impl)

**Files:**
- Create: `agent/tools/spiral_homework/drive_store.py`
- Test: `tests/spiral_homework/test_drive_store.py`

- [ ] **Step 1: Write the failing tests** (FakeDriveClient records calls; no network)

```python
# tests/spiral_homework/test_drive_store.py
from agent.tools.spiral_homework.drive_store import upload_homework, DriveClient

class FakeDriveClient(DriveClient):
    def __init__(self):
        self.folders = {}        # (name, parent) -> id
        self.uploads = []        # (local_path, parent_id, name)
        self.shares = []         # (file_id, email, role)
        self._next = 0
    def ensure_folder(self, name, parent_id):
        key = (name, parent_id)
        if key not in self.folders:
            self._next += 1
            self.folders[key] = f"id{self._next}"
        return self.folders[key]
    def upload_file(self, local_path, parent_id, name):
        self.uploads.append((str(local_path), parent_id, name))
        return f"https://drive.example/{name}"
    def share(self, file_id, email, role="writer"):
        self.shares.append((file_id, email, role))

def test_upload_homework_builds_path_and_shares():
    fake = FakeDriveClient()
    link = upload_homework(fake, "generated/9-12.xlsx", "2025-2026",
                           status="Drafts", share_with="karrie@example.com")
    # folder chain: Nova Teaching Assistant -> Homework -> 2025-2026 -> Drafts
    names = [k[0] for k in fake.folders]
    assert names == ["Nova Teaching Assistant", "Homework", "2025-2026", "Drafts"]
    # uploaded into the Drafts folder
    assert fake.uploads[0][2] == "9-12.xlsx"
    # root shared with Karrie
    root_id = fake.folders[("Nova Teaching Assistant", None)]
    assert (root_id, "karrie@example.com", "writer") in fake.shares
    assert link.startswith("https://drive.example/")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/spiral_homework/test_drive_store.py -v`
Expected: FAIL with `ModuleNotFoundError: ...drive_store`.

- [ ] **Step 3: Implement `drive_store.py`**

```python
# agent/tools/spiral_homework/drive_store.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Protocol

ROOT_FOLDER = "Nova Teaching Assistant"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = os.getenv("NOVA_DRIVE_TOKEN", ".nova_drive_token.json")
CLIENT_SECRET_PATH = os.getenv("NOVA_DRIVE_CLIENT_SECRET", "client_secret.json")

class DriveClient(Protocol):
    def ensure_folder(self, name: str, parent_id: Optional[str]) -> str: ...
    def upload_file(self, local_path: str, parent_id: str, name: str) -> str: ...
    def share(self, file_id: str, email: str, role: str = "writer") -> None: ...

def upload_homework(client: DriveClient, local_path: str, school_year: str,
                    status: str = "Drafts", share_with: Optional[str] = None) -> str:
    """Ensure ROOT/Homework/<year>/<status>, share root with Karrie, upload the file. Returns link."""
    root = client.ensure_folder(ROOT_FOLDER, None)
    if share_with:
        client.share(root, share_with)
    parent = root
    for part in ("Homework", school_year, status):
        parent = client.ensure_folder(part, parent)
    return client.upload_file(local_path, parent, Path(local_path).name)

class GoogleDriveClient:
    """Real DriveClient backed by the Google Drive API (OAuth drive.file)."""
    def __init__(self):
        self._svc = _build_service()
    def ensure_folder(self, name, parent_id):
        q = ("mimeType='application/vnd.google-apps.folder' and trashed=false "
             f"and name='{name}'" + (f" and '{parent_id}' in parents" if parent_id else ""))
        hits = self._svc.files().list(q=q, fields="files(id)", spaces="drive").execute().get("files", [])
        if hits:
            return hits[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            meta["parents"] = [parent_id]
        return self._svc.files().create(body=meta, fields="id").execute()["id"]
    def upload_file(self, local_path, parent_id, name):
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(
            local_path,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        f = self._svc.files().create(
            body={"name": name, "parents": [parent_id]},
            media_body=media, fields="id, webViewLink").execute()
        return f.get("webViewLink", f["id"])
    def share(self, file_id, email, role="writer"):
        try:
            self._svc.permissions().create(
                fileId=file_id, body={"type": "user", "role": role, "emailAddress": email},
                sendNotificationEmail=False).execute()
        except Exception:
            pass  # already shared / non-fatal

def _build_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as fh:
            fh.write(creds.to_json())
    return build("drive", "v3", credentials=creds)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/spiral_homework/test_drive_store.py -v`
Expected: 1 passed. (Only the pure `upload_homework` + Fake are tested; `GoogleDriveClient`/`_build_service` are exercised by the manual smoke test in Task 5.)

- [ ] **Step 5: Commit**

```bash
git add agent/tools/spiral_homework/drive_store.py tests/spiral_homework/test_drive_store.py
git commit -m "feat(spiral): Drive store (protocol + fake + GoogleDriveClient, drive.file)"
```

---

## Task 5: Orchestrator + CLI

**Files:**
- Create: `agent/tools/spiral_homework/__main__.py`
- Modify: `agent/tools/spiral_homework/__init__.py` (add the import deferred from Task 0)
- Test: `tests/spiral_homework/test_orchestrator.py`

- [ ] **Step 1: Write the failing test** (inject fake generator + fake drive; no network)

```python
# tests/spiral_homework/test_orchestrator.py
from agent.tools.spiral_homework.__main__ import generate_spiral_homework
from agent.tools.spiral_homework.models import Box, WeekSpec

def _fake_week(**kw):
    return WeekSpec(due_date="9/12", track=kw.get("track", "regular"), boxes=[
        Box(day="Monday", type="computation", role="current", text="1 5/6 × 4 1/2"),
        Box(day="Monday", type="computation", role="review", text="246.75 ÷ 2.5 ="),
    ])

def test_orchestrator_generates_and_renders_local(tmp_path):
    res = generate_spiral_homework(
        "Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12", "2025-2026",
        track="regular", upload=False, out_dir=tmp_path, _generate=_fake_week)
    assert res["local_path"].exists()
    assert res["local_path"].suffix == ".xlsx"
    assert res["drive_link"] is None

def test_orchestrator_uploads_when_enabled(tmp_path):
    captured = {}
    def fake_upload(local_path, school_year, status="Drafts", share_with=None):
        captured["args"] = (str(local_path), school_year, status)
        return "https://drive.example/wk.xlsx"
    res = generate_spiral_homework(
        "Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12", "2025-2026",
        track="regular", upload=True, out_dir=tmp_path,
        _generate=_fake_week, _upload=fake_upload)
    assert res["drive_link"] == "https://drive.example/wk.xlsx"
    assert captured["args"][1] == "2025-2026"

def test_orchestrator_keeps_local_on_drive_error(tmp_path):
    def boom(*a, **k):
        raise RuntimeError("no creds")
    res = generate_spiral_homework(
        "Fractions", ["6.NS.A.1"], ["6.NS.B.3"], "9/12", "2025-2026",
        upload=True, out_dir=tmp_path, _generate=_fake_week, _upload=boom)
    assert res["local_path"].exists()
    assert res["drive_link"] is None
    assert "no creds" in res["drive_error"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/spiral_homework/test_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError: ...__main__`.

- [ ] **Step 3: Implement `__main__.py`**

```python
# agent/tools/spiral_homework/__main__.py
from __future__ import annotations
import argparse
import os
from pathlib import Path
from .generator import generate_week_spec
from .renderer import render_xlsx

KARRIE_EMAIL = os.getenv("KARRIE_EMAIL", "")

def _default_upload(local_path, school_year, status="Drafts", share_with=None):
    from .drive_store import GoogleDriveClient, upload_homework
    return upload_homework(GoogleDriveClient(), str(local_path), school_year,
                           status=status, share_with=share_with or (KARRIE_EMAIL or None))

def generate_spiral_homework(current_topic, current_standards, review_standards, due_date,
                             school_year, track="regular", upload=True, out_dir="generated",
                             _generate=generate_week_spec, _upload=_default_upload) -> dict:
    week = _generate(current_topic, current_standards, review_standards, due_date, track=track)
    safe_due = due_date.replace("/", "-")
    out_path = Path(out_dir) / f"{safe_due} spiral ({track}).xlsx"
    local = render_xlsx(week, out_path)
    result = {"local_path": local, "drive_link": None}
    if upload:
        try:
            result["drive_link"] = _upload(local, school_year, status="Drafts")
        except Exception as e:
            result["drive_error"] = str(e)
    return result

def main(argv=None):
    p = argparse.ArgumentParser(prog="spiral_homework", description="Generate Karrie's spiral homework")
    p.add_argument("--topic", required=True)
    p.add_argument("--standards", default="", help="current standard codes, comma-separated")
    p.add_argument("--review", default="", help="review standard codes, comma-separated")
    p.add_argument("--due", required=True, help="header label, e.g. 9/12")
    p.add_argument("--year", required=True, help="school year folder, e.g. 2025-2026")
    p.add_argument("--track", choices=["regular", "accelerated", "both"], default="regular")
    p.add_argument("--no-upload", action="store_true")
    p.add_argument("--out-dir", default="generated")
    a = p.parse_args(argv)
    tracks = ["regular", "accelerated"] if a.track == "both" else [a.track]
    cur = [s.strip() for s in a.standards.split(",") if s.strip()]
    rev = [s.strip() for s in a.review.split(",") if s.strip()]
    for tr in tracks:
        res = generate_spiral_homework(a.topic, cur, rev, a.due, a.year, track=tr,
                                       upload=not a.no_upload, out_dir=a.out_dir)
        print(f"[{tr}] local: {res['local_path']}")
        if res.get("drive_link"):
            print(f"[{tr}] drive: {res['drive_link']}")
        elif res.get("drive_error"):
            print(f"[{tr}] drive upload skipped/failed: {res['drive_error']} (local file kept)")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Wire the package export** — set `agent/tools/spiral_homework/__init__.py` to:

```python
"""Spiral Review homework generator (Gemini -> WeekSpec -> .xlsx -> Drive)."""
from .__main__ import generate_spiral_homework  # noqa: F401
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/spiral_homework/test_orchestrator.py -v`
Expected: 3 passed.

- [ ] **Step 6: Run the whole suite**

Run: `pytest tests/spiral_homework -v`
Expected: all pass (models 4, renderer 2, generator 2, drive 1, orchestrator 3).

- [ ] **Step 7: Commit**

```bash
git add agent/tools/spiral_homework/__main__.py agent/tools/spiral_homework/__init__.py tests/spiral_homework/test_orchestrator.py
git commit -m "feat(spiral): orchestrator + CLI (generate->render->upload, local fallback)"
```

---

## Task 6: Docs + manual smoke tests

**Files:**
- Modify: `DEPENDENCIES.md`
- Create: `agent/tools/spiral_homework/README.md`

- [ ] **Step 1: Record deps** — append to `DEPENDENCIES.md` runtime table:

```
| `openpyxl` (>=3.1.0) | Read/write Karrie's spiral homework .xlsx | MIT |
| `google-api-python-client` (>=2.130) | Google Drive upload | Apache-2.0 |
| `google-auth-oauthlib` (>=1.2) | Drive OAuth (drive.file) | Apache-2.0 |
```

- [ ] **Step 2: Write `agent/tools/spiral_homework/README.md`** — run + setup:

```markdown
# Spiral Homework Generator
Generate Karrie's weekly Spiral Review homework as an editable .xlsx, saved to Nova's Drive.

## Run (local only — no Drive)
    python -m agent.tools.spiral_homework --topic "Equations" --due 2/6 --year 2025-2026 \
      --standards 6.EE.B.7 --review 6.NS.B.3,6.RP.A.2 --track both --no-upload
Output: ./generated/2-6 spiral (regular).xlsx and (accelerated).xlsx

## Drive setup (one-time, to drop into Nova's Drive)
1. In Google Cloud project gen-lang-client-0232400708: enable the Drive API; create an OAuth
   client ID (Desktop); download as ./client_secret.json (gitignored).
2. Set KARRIE_EMAIL=<her email> in .env (to auto-share the root folder).
3. Drop `--no-upload` and run; first run opens a browser consent — approve as
   nova-assistant@example.com. Files land in
   "Nova Teaching Assistant / Homework / <year> / Drafts".

Requires GOOGLE_API_KEY in .env (Gemini). Model via HOMEWORK_MODEL (default gemini-2.0-flash).
```

- [ ] **Step 3: Manual smoke (local render, no network)** — run the `--no-upload` command above; open one `.xlsx` in Excel; confirm 4-column grid, header, spiral mix, a Brain Break, figure placeholder. *(This calls Gemini for real — needs GOOGLE_API_KEY; if the model id errors, set HOMEWORK_MODEL.)*

- [ ] **Step 4: Manual smoke (Drive)** — after the one-time setup, run without `--no-upload`; confirm the file appears in Nova's Drive under `Homework/<year>/Drafts` and is shared with Karrie.

- [ ] **Step 5: Commit**

```bash
git add DEPENDENCIES.md agent/tools/spiral_homework/README.md
git commit -m "docs(spiral): dependencies + generator README/run+setup"
```

---

## Self-Review (completed)
- **Spec coverage:** models ✓ (Task 1), Gemini generation w/ spiral mix + retry ✓ (Task 3),
  openpyxl renderer w/ grid+borders+placeholders ✓ (Task 2), Drive `Homework/<year>/Drafts` + share +
  local fallback ✓ (Tasks 4–5), CLI w/ `--track both` + `--no-upload` ✓ (Task 5), tests mock
  network ✓, no student PII (prompt + synthetic tests) ✓, deps recorded ✓ (Task 6). Out-of-scope
  (embedded images, UI, scheduling, ADK wiring) intentionally absent.
- **Placeholders:** none — every code/command step is complete.
- **Type consistency:** `Box`/`WeekSpec` fields, `DriveClient` methods (`ensure_folder`,
  `upload_file`, `share`), `generate_week_spec(..., _call=)`, `upload_homework(client, ..., client=)`,
  and `generate_spiral_homework(..., _generate=, _upload=)` are consistent across tasks.
