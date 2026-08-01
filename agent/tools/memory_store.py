"""Durable profile memory for Nova (Tier 4).

Facts Karrie or Jim explicitly ask Nova to remember ("Nova, remember I do
spiral review on Thursdays") persist in Firestore (collection
``nova_memories``) and are loaded into every session briefing. Falls back to
a local JSONL file when Firestore isn't reachable (offline dev, tests).
NOVA_MEMORY_BACKEND=firestore|csv forces a backend (shared with the request
log; "csv" selects the local-file fallback here too).
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path("docs/00_Inbox_from_Karrie")
MEMORY_FILE = MEMORY_DIR / "Nova_Memories.jsonl"
FIRESTORE_COLLECTION = "nova_memories"
CATEGORIES = ("preference", "schedule", "classroom", "personal", "other")


class _LocalBackend:
    """JSONL-on-disk fallback. Ephemeral on Cloud Run; fine for dev/tests."""
    name = "csv"  # matches the NOVA_MEMORY_BACKEND value that selects it

    def add(self, row: dict) -> None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def all(self) -> list:
        if not MEMORY_FILE.exists():
            return []
        rows = []
        with open(MEMORY_FILE, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def delete_ids(self, ids: list) -> None:
        keep = [r for r in self.all() if r["Memory_ID"] not in ids]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            for r in keep:
                f.write(json.dumps(r) + "\n")


class _FirestoreBackend:
    name = "firestore"

    def __init__(self):
        from google.cloud import firestore
        self._db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT") or None)
        self._col = self._db.collection(FIRESTORE_COLLECTION)

    def add(self, row: dict) -> None:
        self._col.document(row["Memory_ID"]).set(row)

    def all(self) -> list:
        return [doc.to_dict() for doc in self._col.stream()]

    def delete_ids(self, ids: list) -> None:
        for mem_id in ids:
            self._col.document(mem_id).delete()


_BACKEND = None


def _backend():
    global _BACKEND
    if _BACKEND is None:
        mode = os.getenv("NOVA_MEMORY_BACKEND", "").strip().lower()
        if mode == "csv":
            _BACKEND = _LocalBackend()
        elif mode == "firestore":
            _BACKEND = _FirestoreBackend()
        else:
            try:
                _BACKEND = _FirestoreBackend()
            except Exception as exc:
                print(f"[MemoryStore] Firestore unavailable ({exc}); using local fallback.")
                _BACKEND = _LocalBackend()
    return _BACKEND


def _reset_backend():
    """Test hook: force backend re-selection."""
    global _BACKEND
    _BACKEND = None


def save_memory(fact: str, category: str = "other", person: str = "") -> str:
    """Persist a fact Nova was asked to remember. Returns a confirmation with its ID."""
    fact = (fact or "").strip()
    if not fact:
        return "Error: cannot save an empty fact."
    category = (category or "other").strip().lower()
    if category not in CATEGORIES:
        category = "other"
    mem_id = str(uuid.uuid4())[:8]
    _backend().add({
        "Memory_ID": mem_id,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Fact": fact,
        "Category": category,
        "Person": (person or "").strip(),
    })
    return f"Remembered ({category}): {fact} [id {mem_id}]"


def get_memories() -> list:
    """All saved facts, oldest first."""
    rows = _backend().all()
    rows.sort(key=lambda r: r.get("Date", ""))
    return rows


def forget_memory(fact_hint: str) -> str:
    """Delete saved facts whose text contains fact_hint (case-insensitive)."""
    hint = (fact_hint or "").strip().lower()
    if len(hint) < 3:
        return "Error: give a few words of the fact to forget, so I don't delete the wrong thing."
    matches = [r for r in get_memories() if hint in r["Fact"].lower()]
    if not matches:
        return f"No saved fact matches '{fact_hint}'."
    _backend().delete_ids([r["Memory_ID"] for r in matches])
    forgotten = "; ".join(r["Fact"] for r in matches)
    return f"Forgot {len(matches)} fact(s): {forgotten}"


def format_memories_briefing() -> str:
    """Known-facts block for the session briefing ('' when nothing saved)."""
    rows = get_memories()
    if not rows:
        return ""
    lines = ["Known facts (things you've been asked to remember):"]
    for r in rows:
        who = f" — about/from {r['Person']}" if r.get("Person") else ""
        lines.append(f"- [{r.get('Category', 'other')}] {r['Fact']}{who}")
    return "\n".join(lines)
