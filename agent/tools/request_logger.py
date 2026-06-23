"""Request Logger Tool for Nova."""
import csv
import os
import uuid
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("docs/00_Inbox_from_Karrie")
LOG_FILE = LOG_DIR / "Nova_Request_Log.csv"
FIELDNAMES = ["Task_ID", "Date", "Topic", "Standard_Code", "Status", "File_ID"]

def _ensure_log_exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def log_nova_task(topic: str, standard_code: str, status: str = "Open", file_id: str = "") -> str:
    """Log a new request/task into the Nova Request Log CSV. Returns the generated Task_ID."""
    _ensure_log_exists()
    task_id = str(uuid.uuid4())[:8]
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "Task_ID": task_id,
            "Date": date_str,
            "Topic": topic,
            "Standard_Code": standard_code,
            "Status": status,
            "File_ID": file_id
        })
    
    return f"Task logged successfully. Task_ID: {task_id}"

def update_task_status(task_id: str, new_status: str) -> str:
    """Update the status of an existing task in the Nova Request Log CSV (e.g., to 'Completed' or 'Approved')."""
    _ensure_log_exists()
    
    rows = []
    updated = False
    
    with open(LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Task_ID"] == task_id:
                row["Status"] = new_status
                updated = True
            rows.append(row)
            
    if not updated:
        return f"Error: Task_ID {task_id} not found."
        
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
        
    return f"Task_ID {task_id} status updated to '{new_status}'."

def get_recent_requests(limit: int = 5) -> str:
    """Return the most recent requests logged in the Nova Request Log, to help Nova recall recent topics."""
    if not LOG_FILE.exists():
        return "The request log is currently empty. No recent topics."
        
    rows = []
    with open(LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            
    if not rows:
        return "The request log is currently empty. No recent topics."
        
    recent = rows[-limit:]
    lines = ["Recent requests:"]
    for r in recent:
        lines.append(f"- Task {r['Task_ID']}: Topic '{r['Topic']}' (Standard: {r['Standard_Code']}), Status: {r['Status']}")
        
    return "\n".join(lines)
