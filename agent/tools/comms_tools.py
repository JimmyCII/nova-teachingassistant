import csv
from pathlib import Path
from agent.tools.request_logger import update_task_status, LOG_FILE

def check_pending_approvals() -> str:
    """Iterate through the request log and check if any 'Pending Approval' tasks have been approved."""
    if not LOG_FILE.exists():
        return "No request log found."

    try:
        from mcp_servers.comms_server.server import check_drive_approvals
        
        updates = []
        rows = []
        with open(LOG_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Status") == "Pending Approval" and row.get("File_ID"):
                    res = check_drive_approvals(row["File_ID"])
                    if res.get("approved"):
                        row["Status"] = "Approved"
                        updates.append(row["Task_ID"])
                rows.append(row)
        
        if updates:
            # We rewrite the file with the updated rows
            from agent.tools.request_logger import FIELDNAMES
            with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()
                writer.writerows(rows)
            return f"Found and updated {len(updates)} approved tasks: {', '.join(updates)}"
        else:
            return "No new approvals found."
            
    except Exception as e:
        return f"Failed to check pending approvals: {e}"
