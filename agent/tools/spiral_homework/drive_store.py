# agent/tools/spiral_homework/drive_store.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Protocol

ROOT_FOLDER = "Nova Teaching Assistant"
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send"
]
TOKEN_PATH = os.getenv("NOVA_DRIVE_TOKEN", ".nova_drive_token.json")
CLIENT_SECRET_PATH = os.getenv("NOVA_DRIVE_CLIENT_SECRET", "client_secret.json")

class DriveClient(Protocol):
    def ensure_folder(self, name: str, parent_id: Optional[str]) -> str: ...
    def upload_file(self, local_path: str, parent_id: str, name: str) -> tuple[str, str]: ...
    def share(self, file_id: str, email: str, role: str = "writer") -> None: ...

def upload_homework(client: DriveClient, local_path: str, school_year: str,
                    status: str = "Drafts", share_with: Optional[str] = None) -> tuple[str, str]:
    """Ensure ROOT/Homework/<year>/<status>, share root with Karrie, upload the file. Returns link."""
    root = client.ensure_folder(ROOT_FOLDER, None)
    if share_with:
        client.share(root, share_with)
    parent = client.ensure_folder("Homework", root)
    client.ensure_folder("02_Approved", parent) # Create empty approved folder so it exists
    parent = client.ensure_folder("01_Drafts", parent)
    return client.upload_file(local_path, parent, Path(local_path).name)

class GoogleDriveClient:
    """Real DriveClient backed by the Google Drive API (OAuth drive.file)."""
    def __init__(self):
        from googleapiclient.discovery import build
        self._creds = _get_creds()
        self._svc = build("drive", "v3", credentials=self._creds)
    def ensure_folder(self, name, parent_id):
        q = ("mimeType='application/vnd.google-apps.folder' and trashed=false "
             f"and name='{name}'" + (f" and '{parent_id}' in parents" if parent_id else ""))
        hits = self._svc.files().list(q=q, fields="files(id)", spaces="drive").execute().get("files", [])
        if hits:
            return hits[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            meta["parents"] = [parent_id]
        return self._svc.files().create(body=meta, fields="id").execute()["id"]
    def upload_file(self, local_path, parent_id, name):
        import mimetypes
        from googleapiclient.http import MediaFileUpload
        
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            if str(local_path).endswith('.md'):
                mime_type = "text/markdown"
                
        media = MediaFileUpload(
            local_path,
            mimetype=mime_type)
        file_meta = {"name": name, "parents": [parent_id]}
        file = self._svc.files().create(body=file_meta, media_body=media, fields="id, webViewLink").execute()
        return file.get("webViewLink"), file.get("id")

    def is_in_approved(self, file_id: str) -> bool:
        """Check if the given file has been moved into an 02_Approved folder."""
        meta = self._svc.files().get(fileId=file_id, fields="parents").execute()
        for pid in meta.get("parents", []):
            name = self._svc.files().get(fileId=pid, fields="name").execute().get("name")
            if name == "02_Approved":
                return True
        return False

    def share(self, file_id, email, role="writer"):
        try:
            self._svc.permissions().create(
                fileId=file_id, body={"type": "user", "role": role, "emailAddress": email},
                sendNotificationEmail=False).execute()
        except Exception:
            pass  # already shared / non-fatal

def _get_creds():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as fh:
            fh.write(creds.to_json())
    return creds
