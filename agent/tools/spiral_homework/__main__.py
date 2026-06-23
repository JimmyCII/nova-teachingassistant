# agent/tools/spiral_homework/__main__.py
from __future__ import annotations
import argparse
import os
from pathlib import Path
from .generator import generate_week_spec
from .renderer import render_xlsx

def _default_upload(local_path, school_year, status="Drafts", share_with=None):
    from .drive_store import GoogleDriveClient, upload_homework
    return upload_homework(GoogleDriveClient(), str(local_path), school_year,
                           status=status,
                           share_with=share_with or (os.getenv("KARRIE_EMAIL") or None))

def generate_spiral_homework(current_topic, current_standards, review_standards, due_date,
                             school_year, track="regular", upload=True, out_dir="generated",
                             _generate=generate_week_spec, _upload=_default_upload) -> dict:
    week = _generate(current_topic, current_standards, review_standards, due_date, track=track)
    safe_due = due_date.replace("/", "-")
    out_path = Path(out_dir) / f"{safe_due} spiral ({track}).xlsx"
    local = render_xlsx(week, out_path)
    result = {"local_path": str(local), "drive_link": None}
    if upload:
        try:
            link, file_id = _upload(local, school_year, status="Drafts")
            result["drive_link"] = link
            
            try:
                from mcp_servers.comms_server.server import send_draft_for_approval
                from agent.tools.request_logger import log_nova_task
                karrie_email = os.environ.get("KARRIE_EMAIL", "test@example.com")
                title = f"{current_topic} ({track})"
                send_res = send_draft_for_approval(karrie_email, link, out_path.name, title)
                std_code = current_standards[0] if current_standards else "Homework"
                log_res = log_nova_task(title, std_code, status="Pending Approval", file_id=file_id)
                print("Comms Loop executed:", send_res, log_res)
            except Exception as comms_e:
                print("Warning: Failed to execute comms loop for Homework:", comms_e)
                
        except Exception as e:
            result["drive_error"] = str(e)
    return result

def main(argv=None):
    from dotenv import load_dotenv
    load_dotenv()  # pick up GOOGLE_API_KEY / KARRIE_EMAIL / HOMEWORK_MODEL from .env
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
