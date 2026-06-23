# tests/spiral_homework/test_orchestrator.py
from agent.tools.spiral_homework.__main__ import generate_spiral_homework
from agent.tools.spiral_homework.models import Box, WeekSpec

def _fake_week(*args, **kw):
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
        return "https://drive.example/wk.xlsx", "fake_id"
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
