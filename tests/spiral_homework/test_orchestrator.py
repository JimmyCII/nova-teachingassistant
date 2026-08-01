# tests/spiral_homework/test_orchestrator.py
from datetime import date
from pathlib import Path

import pytest

from agent.tools.spiral_homework.__main__ import (
    DEFAULT_REVIEW_STANDARDS,
    _default_school_year,
    generate_spiral_homework,
)
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
    assert Path(res["local_path"]).exists()
    assert Path(res["local_path"]).suffix == ".xlsx"
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
    assert Path(res["local_path"]).exists()
    assert res["drive_link"] is None
    assert "no creds" in res["drive_error"]


def test_default_school_year_rolls_over_in_july():
    assert _default_school_year(date(2026, 8, 1)) == "2026-2027"
    assert _default_school_year(date(2026, 7, 1)) == "2026-2027"
    assert _default_school_year(date(2026, 3, 15)) == "2025-2026"


def test_orchestrator_requires_due_date():
    with pytest.raises(ValueError):
        generate_spiral_homework("Fractions", ["6.NS.A.1"], upload=False,
                                 _generate=_fake_week)


def test_orchestrator_auto_selects_review_from_recent_log(tmp_path, monkeypatch):
    import agent.tools.request_logger as request_logger
    monkeypatch.setattr(request_logger, "get_recent_standard_codes",
                        lambda limit=10: ["6.NS.A.1", "6.RP.A.3", "6.EE.B.5"])
    captured = {}
    def capture_week(topic, current, review, due, track="regular"):
        captured["review"] = review
        return _fake_week(track=track)
    res = generate_spiral_homework(
        "Fractions", ["6.NS.A.1"], due_date="Friday August 7th",
        upload=False, out_dir=tmp_path, _generate=capture_week)
    # current standard excluded, capped at two picks
    assert captured["review"] == ["6.RP.A.3", "6.EE.B.5"]
    assert Path(res["local_path"]).exists()


def test_orchestrator_falls_back_to_default_review_when_log_empty(tmp_path, monkeypatch):
    import agent.tools.request_logger as request_logger
    monkeypatch.setattr(request_logger, "get_recent_standard_codes", lambda limit=10: [])
    captured = {}
    def capture_week(topic, current, review, due, track="regular"):
        captured["review"] = review
        return _fake_week(track=track)
    generate_spiral_homework(
        "Fractions", ["6.NS.A.1"], due_date="9/12",
        upload=False, out_dir=tmp_path, _generate=capture_week)
    assert captured["review"] == DEFAULT_REVIEW_STANDARDS
