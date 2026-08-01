"""Request Logger Tool for Nova.

Tier-1 durable memory: rows live in Firestore (collection ``nova_request_log``)
so they survive Cloud Run cold starts and are shared across instances. Falls
back to the original local CSV when Firestore isn't reachable (offline dev,
tests). Force a backend with NOVA_MEMORY_BACKEND=firestore|csv.
"""
import csv
import os
import uuid
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("docs/00_Inbox_from_Karrie")
LOG_FILE = LOG_DIR / "Nova_Request_Log.csv"
FIELDNAMES = ["Task_ID", "Date", "Topic", "Standard_Code", "Status", "File_ID"]
FIRESTORE_COLLECTION = "nova_request_log"


class _CsvBackend:
    """Original local-disk backend. Ephemeral on Cloud Run; fine for dev/tests."""
    name = "csv"

    def _ensure_log_exists(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if not LOG_FILE.exists():
            with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()

    def add(self, row: dict) -> None:
        self._ensure_log_exists()
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)

    def update_status(self, task_id: str, new_status: str) -> bool:
        self._ensure_log_exists()
        rows, updated = [], False
        with open(LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["Task_ID"] == task_id:
                    row["Status"] = new_status
                    updated = True
                rows.append(row)
        if updated:
            with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows)
        return updated

    def recent(self, limit: int) -> list:
        """Most recent rows in chronological order (oldest of the batch first)."""
        if not LOG_FILE.exists():
            return []
        with open(LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        return rows[-limit:]


class _FirestoreBackend:
    """Durable backend. Uses ADC (Cloud Run service account / local gcloud ADC)."""
    name = "firestore"

    def __init__(self):
        from google.cloud import firestore
        self._fs = firestore
        # Cloud Run auto-detects the project; local dev sets GOOGLE_CLOUD_PROJECT in .env.
        self._db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT") or None)
        self._col = self._db.collection(FIRESTORE_COLLECTION)

    def add(self, row: dict) -> None:
        self._col.document(row["Task_ID"]).set(row)

    def update_status(self, task_id: str, new_status: str) -> bool:
        ref = self._col.document(task_id)
        if not ref.get().exists:
            return False
        ref.update({"Status": new_status})
        return True

    def recent(self, limit: int) -> list:
        # "Date" is "%Y-%m-%d %H:%M:%S", so lexicographic order == chronological.
        query = (self._col.order_by("Date", direction=self._fs.Query.DESCENDING)
                 .limit(limit))
        rows = [doc.to_dict() for doc in query.stream()]
        rows.reverse()  # chronological, matching the CSV tail
        return rows


_BACKEND = None


def _backend():
    global _BACKEND
    if _BACKEND is None:
        mode = os.getenv("NOVA_MEMORY_BACKEND", "").strip().lower()
        if mode == "csv":
            _BACKEND = _CsvBackend()
        elif mode == "firestore":
            _BACKEND = _FirestoreBackend()
        else:
            try:
                _BACKEND = _FirestoreBackend()
            except Exception as exc:
                print(f"[RequestLog] Firestore unavailable ({exc}); using local CSV fallback.")
                _BACKEND = _CsvBackend()
    return _BACKEND


def _reset_backend():
    """Test hook: force backend re-selection (e.g. after env changes)."""
    global _BACKEND
    _BACKEND = None


def log_nova_task(topic: str, standard_code: str, status: str = "Open", file_id: str = "") -> str:
    """Log a new request/task into the Nova Request Log. Returns the generated Task_ID."""
    task_id = str(uuid.uuid4())[:8]
    _backend().add({
        "Task_ID": task_id,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Topic": topic,
        "Standard_Code": standard_code,
        "Status": status,
        "File_ID": file_id,
    })
    return f"Task logged successfully. Task_ID: {task_id}"


def update_task_status(task_id: str, new_status: str) -> str:
    """Update the status of an existing task in the Nova Request Log (e.g., to 'Completed' or 'Approved')."""
    if not _backend().update_status(task_id, new_status):
        return f"Error: Task_ID {task_id} not found."
    return f"Task_ID {task_id} status updated to '{new_status}'."


def get_recent_requests(limit: int = 5) -> str:
    """Return the most recent requests logged in the Nova Request Log, to help Nova recall recent topics."""
    rows = _backend().recent(limit)
    if not rows:
        return "The request log is currently empty. No recent topics."
    lines = ["Recent requests:"]
    for r in rows:
        lines.append(f"- Task {r['Task_ID']}: Topic '{r['Topic']}' (Standard: {r['Standard_Code']}), Status: {r['Status']} ({r.get('Date', '')})")
    return "\n".join(lines)


def get_recent_standard_codes(limit: int = 10) -> list:
    """Distinct standard codes from the most recent log entries, newest first.

    Skips placeholder values (real AZ codes contain dots, e.g. '6.NS.A.1').
    """
    rows = _backend().recent(50)
    codes = []
    for row in reversed(rows):
        code = (row.get("Standard_Code") or "").strip()
        if code and "." in code and code not in codes:
            codes.append(code)
        if len(codes) >= limit:
            break
    return codes
