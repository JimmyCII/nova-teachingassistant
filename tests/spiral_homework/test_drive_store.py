# tests/spiral_homework/test_drive_store.py
from agent.tools.spiral_homework.drive_store import upload_homework, DriveClient

class FakeDriveClient(DriveClient):
    def __init__(self):
        self.folders = {}        # (name, parent) -> id
        self.uploads = []        # (local_path, parent_id, name)
        self.shares = []         # (file_id, email, role)
        self._next = 0
    def ensure_folder(self, name, parent_id):
        key = (name, parent_id)
        if key not in self.folders:
            self._next += 1
            self.folders[key] = f"id{self._next}"
        return self.folders[key]
    def upload_file(self, local_path, parent_id, name):
        self.uploads.append((str(local_path), parent_id, name))
        return f"https://drive.example/{name}"
    def share(self, file_id, email, role="writer"):
        self.shares.append((file_id, email, role))

def test_upload_homework_builds_path_and_shares():
    fake = FakeDriveClient()
    link = upload_homework(fake, "generated/9-12.xlsx", "2025-2026",
                           status="Drafts", share_with="karrie@example.com")
    # folder chain: Nova Teaching Assistant -> Homework -> 02_Approved -> 01_Drafts
    names = [k[0] for k in fake.folders]
    assert names == ["Nova Teaching Assistant", "Homework", "02_Approved", "01_Drafts"]
    # uploaded into the Drafts folder
    assert fake.uploads[0][2] == "9-12.xlsx"
    # root shared with Karrie
    root_id = fake.folders[("Nova Teaching Assistant", None)]
    assert (root_id, "karrie@example.com", "writer") in fake.shares
    assert link.startswith("https://drive.example/")
