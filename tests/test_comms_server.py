import pytest
from unittest.mock import patch, MagicMock
from mcp_servers.comms_server.server import send_draft_for_approval, check_drive_approvals

def test_send_draft():
    # Test the real send or mock fallback works
    res = send_draft_for_approval("test@example.com", "http://link", "Doc1", "Math")
    assert "Mock Fallback" in res or "Email sent successfully" in res

@patch('mcp_servers.comms_server.server.GoogleDriveClient')
def test_check_drive_approvals(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Test True path
    mock_client.is_in_approved.return_value = True
    res = check_drive_approvals("file_123")
    assert res["approved"] is True
    
    # Test False path
    mock_client.is_in_approved.return_value = False
    res = check_drive_approvals("file_456")
    assert res["approved"] is False
