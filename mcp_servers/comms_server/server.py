import os
import base64
from email.message import EmailMessage
from mcp.server.fastmcp import FastMCP
from agent.tools.spiral_homework.drive_store import GoogleDriveClient
from googleapiclient.discovery import build

mcp = FastMCP("Comms Server")

@mcp.tool()
def send_draft_for_approval(to_email: str, drive_link: str, doc_name: str, topic: str) -> str:
    """Email Karrie a link to review/approve a draft. Curriculum content only — never student PII."""
    sender_email = os.environ.get("SENDER_EMAIL", "nova-assistant@example.com")
    try:
        client = GoogleDriveClient()
        creds = client._creds
        
        service = build('gmail', 'v1', credentials=creds)
        
        message = EmailMessage()
        message.set_content(f"Hi Karrie,\n\nNova has generated a new draft for '{topic}' ({doc_name}).\n\nPlease review the draft here: {drive_link}\n\nTo approve this draft, simply move the file into the '03_Approved' folder in Google Drive.\n\nThanks,\nNova (TeacherMind)")
        
        message['To'] = to_email
        message['From'] = sender_email
        message['Subject'] = f"Nova Draft for Review: {doc_name}"
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"REAL EMAIL: Sending approval request to {to_email} for {doc_name}")
        return f"Email sent successfully to {to_email} (Message ID: {send_message['id']})"
    except Exception as e:
        print(f"Gmail API Failed: {e}")
        print(f"MOCK EMAIL FALLBACK: Sending approval request to {to_email} for {doc_name} ({topic}) at {drive_link}")
        return f"Mock Fallback (Gmail error): Email 'sent' to {to_email} with link {drive_link}"

def send_admin_alert_email(admin_email: str, details: str) -> str:
    """Send an immediate security alert to the admin email."""
    sender_email = os.environ.get("SENDER_EMAIL", "nova-assistant@example.com")
    try:
        client = GoogleDriveClient()
        service = build('gmail', 'v1', credentials=client._creds)
        
        message = EmailMessage()
        message.set_content(f"SECURITY ALERT from Nova Voice Console:\n\n{details}\n\nPlease investigate immediately.")
        
        message['To'] = admin_email
        message['From'] = sender_email
        message['Subject'] = "🚨 URGENT: Nova Security Alert"
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"🚨 SENT ADMIN ALERT TO {admin_email}")
        return f"Alert sent successfully."
    except Exception as e:
        print(f"Failed to send Admin Alert via Gmail API: {e}")
        return f"Alert fallback printed: {details}"

@mcp.tool()
def check_drive_approvals(file_id: str) -> dict:
    """PULL: has Karrie moved this file into 03_Approved? Returns {"approved": bool}."""
    client = GoogleDriveClient()
    return {"approved": client.is_in_approved(file_id)}

if __name__ == "__main__":
    mcp.run(transport="stdio")
