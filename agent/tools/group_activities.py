"""Group Activities (DOK) Generator Tool."""
import os
from pathlib import Path
from google import genai

_MODEL = os.getenv("HOMEWORK_MODEL", "gemini-2.5-flash")

_PROMPT = """You create a DOK (Depth of Knowledge) leveled Group Activity for a 6th-grade Arizona math class based on the provided standard.
Format the output as clean Markdown.

Structure:
1. DOK 1 (Recall): A simple warm-up activity for the group.
2. DOK 2 (Skill/Concept): A collaborative problem-solving task.
3. DOK 3 (Strategic Thinking): A complex, open-ended challenge.
Assign specific roles for group members (e.g., Facilitator, Recorder, Presenter).

Standard to cover: {standard}
Topic: {topic}
"""

def generate_dok_activity(standard: str, topic: str) -> dict:
    """Generate a DOK-leveled group activity and save it as a Markdown file."""
    prompt = _PROMPT.format(standard=standard, topic=topic)
    
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(model=_MODEL, contents=prompt)
    
    out_dir = Path("docs/02_Generated/Assessments_DOK")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    safe_topic = topic.replace("/", "-").replace("\\", "-").replace(" ", "_")
    out_path = out_dir / f"{safe_topic}_DOK_Activity.md"
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(response.text)
        
    try:
        from agent.tools.spiral_homework.drive_store import GoogleDriveClient
        client = GoogleDriveClient()
        root = client.ensure_folder("Nova Teaching Assistant", None)
        activities_folder = client.ensure_folder("Group Activities", root)
        client.ensure_folder("02_Approved", activities_folder) # Create empty approved folder so it exists
        drafts_folder = client.ensure_folder("01_Drafts", activities_folder)
        link, file_id = client.upload_file(str(out_path), drafts_folder, out_path.name)
        
        try:
            from mcp_servers.comms_server.server import send_draft_for_approval
            from agent.tools.request_logger import log_nova_task
            karrie_email = os.environ.get("KARRIE_EMAIL", "test@example.com")
            send_res = send_draft_for_approval(karrie_email, link, out_path.name, topic)
            log_res = log_nova_task(topic, standard, status="Pending Approval", file_id=file_id)
            print("Comms Loop executed:", send_res, log_res)
        except Exception as comms_e:
            print("Warning: Failed to execute comms loop for Group Activity:", comms_e)
            
        return {
            "status": "success",
            "local_path": str(out_path),
            "drive_link": link,
            "message": f"DOK Activity generated and uploaded to Google Drive: {link}"
        }
    except Exception as e:
        return {
            "status": "success",
            "local_path": str(out_path),
            "message": f"DOK Activity generated locally to {out_path}, but Drive upload failed: {e}"
        }
