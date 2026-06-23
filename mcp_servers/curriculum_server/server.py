import os
import json
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# Create a FastMCP server
mcp = FastMCP("Curriculum Server")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "agent" / "data"

@mcp.resource("standards://az-math-6")
def get_az_math_6_standards() -> str:
    """Return the Arizona Math 6 standards as a JSON string."""
    standards_file = DATA_DIR / "az_math_6_standards.json"
    if standards_file.exists():
        with open(standards_file, "r", encoding="utf-8") as f:
            return f.read()
    return "{}"

@mcp.resource("dok://webb-model")
def get_webb_model() -> str:
    """Return the official AZED DOK Webb model definition."""
    dok_file = DATA_DIR / "az_dok_levels.json"
    if dok_file.exists():
        with open(dok_file, "r", encoding="utf-8") as f:
            return f.read()
    return "{}"

@mcp.tool()
def save_draft(local_path: str, kind: str, topic: str) -> str:
    """Uploads a generated file to the appropriate Google Drive folder."""
    try:
        from agent.tools.spiral_homework.drive_store import GoogleDriveClient
        client = GoogleDriveClient()
        root = client.ensure_folder("Nova Teaching Assistant", None)
        generated = client.ensure_folder("02_Generated", root)
        kind_folder = client.ensure_folder(kind, generated)
        topic_folder = client.ensure_folder(topic, kind_folder)
        
        path_obj = Path(local_path)
        link = client.upload_file(local_path, topic_folder, path_obj.name)
        return link
    except Exception as e:
        return f"Error uploading to drive: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
