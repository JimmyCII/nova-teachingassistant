# tests/test_memory_store.py
import pytest

from agent.tools import memory_store as ms


@pytest.fixture
def local_mem(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(ms, "MEMORY_FILE", tmp_path / "mem.jsonl")
    monkeypatch.setattr(ms, "_BACKEND", ms._LocalBackend())
    yield
    ms._reset_backend()


def test_save_and_list_and_format(local_mem):
    res = ms.save_memory("Karrie does spiral review on Thursdays", "schedule", "Karrie")
    assert "Remembered (schedule)" in res

    rows = ms.get_memories()
    assert len(rows) == 1
    assert rows[0]["Person"] == "Karrie"

    text = ms.format_memories_briefing()
    assert "[schedule]" in text
    assert "Thursdays" in text
    assert "Karrie" in text


def test_save_rejects_empty_and_normalizes_category(local_mem):
    assert "Error" in ms.save_memory("   ")
    ms.save_memory("Jim handles the technical side", "totally-made-up", "Jim")
    assert ms.get_memories()[0]["Category"] == "other"


def test_forget_by_hint(local_mem):
    ms.save_memory("Karrie does spiral review on Thursdays", "schedule", "Karrie")
    ms.save_memory("Jim is Karrie's husband", "personal", "Jim")

    assert "Error" in ms.forget_memory("ab")            # hint too short
    assert "No saved fact" in ms.forget_memory("zzz never said")

    res = ms.forget_memory("spiral review")
    assert "Forgot 1 fact" in res
    remaining = ms.get_memories()
    assert len(remaining) == 1
    assert "husband" in remaining[0]["Fact"]


def test_format_empty_is_blank(local_mem):
    assert ms.format_memories_briefing() == ""


# ---------- Firestore backend against an in-memory fake ----------

class FakeSnapshot:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return dict(self._data)


class FakeCollection:
    def __init__(self, store):
        self._store = store

    def document(self, doc_id):
        col = self

        class Ref:
            def set(self, row):
                col._store[doc_id] = dict(row)

            def delete(self):
                col._store.pop(doc_id, None)

        return Ref()

    def stream(self):
        return [FakeSnapshot(r) for r in self._store.values()]


@pytest.fixture
def fs_mem(monkeypatch):
    store = {}
    backend = object.__new__(ms._FirestoreBackend)
    backend._col = FakeCollection(store)
    monkeypatch.setattr(ms, "_BACKEND", backend)
    yield store
    ms._reset_backend()


def test_firestore_save_format_forget(fs_mem):
    ms.save_memory("Karrie prefers warm parent-message tone", "preference", "Karrie")
    ms.save_memory("Jim set up my Google Drive", "personal", "Jim")
    assert len(fs_mem) == 2
    assert "warm parent-message" in ms.format_memories_briefing()

    assert "Forgot 1 fact" in ms.forget_memory("Google Drive")
    assert len(fs_mem) == 1


# ---------- Requested_By on the request log ----------

def test_log_task_records_requester(tmp_path, monkeypatch):
    from agent.tools import request_logger as rl
    monkeypatch.setattr(rl, "LOG_DIR", tmp_path)
    monkeypatch.setattr(rl, "LOG_FILE", tmp_path / "log.csv")
    monkeypatch.setattr(rl, "_BACKEND", rl._CsvBackend())
    try:
        rl.log_nova_task("Ratios", "6.RP.A.1", requested_by="Jim")
        rl.log_nova_task("Fractions", "6.NS.A.1")  # anonymous — no requester shown
        text = rl.get_recent_requests()
        assert "requested by Jim" in text
        assert text.count("requested by") == 1
    finally:
        rl._reset_backend()


# ---------- Briefing includes saved facts ----------

def test_briefing_includes_known_facts(monkeypatch):
    import web.briefing as briefing
    monkeypatch.setattr(briefing, "get_recent_requests", lambda limit=8: "Recent requests:\n- x")
    monkeypatch.setattr(briefing, "format_memories_briefing",
                        lambda: "Known facts (things you've been asked to remember):\n- [schedule] Thursdays")
    text = briefing.build_briefing()
    assert "Known facts" in text
    assert "Thursdays" in text


def test_briefing_survives_facts_failure(monkeypatch):
    import web.briefing as briefing
    monkeypatch.setattr(briefing, "get_recent_requests", lambda limit=8: "Recent requests:\n- x")
    def boom():
        raise RuntimeError("nope")
    monkeypatch.setattr(briefing, "format_memories_briefing", boom)
    text = briefing.build_briefing()
    assert "Session briefing" in text
    assert "Saved facts unavailable" in text
