# tests/test_request_logger.py
from pathlib import Path

import pytest

from agent.tools import request_logger as rl


@pytest.fixture
def csv_log(tmp_path, monkeypatch):
    """Point the CSV backend at a throwaway file and select it explicitly."""
    monkeypatch.setattr(rl, "LOG_DIR", tmp_path)
    monkeypatch.setattr(rl, "LOG_FILE", tmp_path / "log.csv")
    monkeypatch.setattr(rl, "_BACKEND", rl._CsvBackend())
    yield
    rl._reset_backend()


def test_csv_roundtrip_log_update_recent(csv_log):
    res = rl.log_nova_task("Dividing Fractions", "6.NS.A.1")
    task_id = res.split("Task_ID: ")[1]
    assert "logged successfully" in res

    assert "not found" in rl.update_task_status("nope", "Completed")
    assert "updated to 'Completed'" in rl.update_task_status(task_id, "Completed")

    recent = rl.get_recent_requests()
    assert "Dividing Fractions" in recent
    assert "Completed" in recent


def test_csv_empty_log_message(csv_log):
    assert "currently empty" in rl.get_recent_requests()
    assert rl.get_recent_standard_codes() == []


def test_csv_recent_standard_codes_newest_first_distinct(csv_log):
    rl.log_nova_task("A", "6.NS.A.1")
    rl.log_nova_task("B", "6.RP.A.3")
    rl.log_nova_task("C", "Homework")     # placeholder — no dot, skipped
    rl.log_nova_task("D", "6.RP.A.3")     # duplicate — kept once, newest position
    codes = rl.get_recent_standard_codes()
    assert codes == ["6.RP.A.3", "6.NS.A.1"]


# ---------- Firestore backend against an in-memory fake ----------

class FakeSnapshot:
    def __init__(self, data):
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data)


class FakeDocRef:
    def __init__(self, store, doc_id):
        self._store, self._id = store, doc_id

    def set(self, row):
        self._store[self._id] = dict(row)

    def get(self):
        return FakeSnapshot(self._store.get(self._id))

    def update(self, fields):
        self._store[self._id].update(fields)


class FakeCollection:
    def __init__(self, store):
        self._store = store
        self._limit = None

    def document(self, doc_id):
        return FakeDocRef(self._store, doc_id)

    def order_by(self, field, direction=None):
        assert field == "Date"
        return self

    def limit(self, n):
        self._limit = n
        return self

    def stream(self):
        rows = sorted(self._store.values(), key=lambda r: r["Date"], reverse=True)
        return [FakeSnapshot(r) for r in rows[: self._limit]]


class FakeFsModule:
    class Query:
        DESCENDING = "DESCENDING"


@pytest.fixture
def fs_log(monkeypatch):
    store = {}
    backend = object.__new__(rl._FirestoreBackend)
    backend._fs = FakeFsModule
    backend._col = FakeCollection(store)
    monkeypatch.setattr(rl, "_BACKEND", backend)
    yield store
    rl._reset_backend()


def test_firestore_roundtrip(fs_log):
    res = rl.log_nova_task("Ratios", "6.RP.A.1")
    task_id = res.split("Task_ID: ")[1]
    assert task_id in fs_log

    assert "updated to 'Approved'" in rl.update_task_status(task_id, "Approved")
    assert fs_log[task_id]["Status"] == "Approved"
    assert "not found" in rl.update_task_status("missing", "Approved")

    recent = rl.get_recent_requests()
    assert "Ratios" in recent and "Approved" in recent


def test_firestore_recent_is_chronological_and_limited(fs_log):
    for i in range(7):
        fs_log[f"t{i}"] = {"Task_ID": f"t{i}", "Date": f"2026-08-01 10:0{i}:00",
                           "Topic": f"topic{i}", "Standard_Code": "6.NS.A.1",
                           "Status": "Open", "File_ID": ""}
    text = rl.get_recent_requests(limit=3)
    # newest three, listed oldest-first (chronological), matching CSV behavior
    assert "topic4" in text and "topic6" in text
    assert "topic3" not in text
    assert text.index("topic4") < text.index("topic6")


def test_backend_env_selection_csv(monkeypatch):
    monkeypatch.setenv("NOVA_MEMORY_BACKEND", "csv")
    rl._reset_backend()
    assert rl._backend().name == "csv"
    rl._reset_backend()


# ---------- Tier-2 briefing ----------

def test_briefing_includes_recent_requests(monkeypatch):
    import web.briefing as briefing
    monkeypatch.setattr(briefing, "get_recent_requests",
                        lambda limit=8: "Recent requests:\n- Task ab: Topic 'Ratios'")
    text = briefing.build_briefing()
    assert "Session briefing" in text
    assert "Ratios" in text
    assert "Today's date" in text


def test_briefing_survives_log_failure(monkeypatch):
    import web.briefing as briefing
    def boom(limit=8):
        raise RuntimeError("firestore down")
    monkeypatch.setattr(briefing, "get_recent_requests", boom)
    text = briefing.build_briefing()
    assert "Session briefing" in text
    assert "unavailable" in text
