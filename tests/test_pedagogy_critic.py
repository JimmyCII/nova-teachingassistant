import pytest
from unittest.mock import patch, MagicMock
import json
from agent.tools.pedagogy_critic import review_and_revise

def mock_provider_success():
    return '{"standard": "TEST_STANDARD"}'

def mock_provider_fail():
    raise Exception("Simulated MCP Failure")

@patch('agent.tools.pedagogy_critic.genai.Client')
def test_critic_with_mock_provider(mock_client_class):
    # Mock the Gemini client response
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "verdict": "revised",
        "issues": ["Fixed rigor"],
        "revised_text": "Q1: New DOK 2 Question"
    })
    mock_client.models.generate_content.return_value = mock_response

    # Test that the critic correctly identifies the provider
    res = review_and_revise("Draft quiz text", _standards_provider=mock_provider_success)
    assert res.get("standards_source") == "mcp"
    assert res.get("verdict") == "revised"

@patch('agent.tools.pedagogy_critic.genai.Client')
def test_critic_fallback(mock_client_class):
    # Mock the Gemini client response
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "verdict": "revised",
        "issues": ["Fixed rigor"],
        "revised_text": "Q1: New DOK 2 Question"
    })
    mock_client.models.generate_content.return_value = mock_response

    # Test that a failing provider triggers disk-fallback
    res = review_and_revise("Draft quiz text", _standards_provider=mock_provider_fail)
    assert res.get("standards_source") == "disk-fallback"
    assert res.get("verdict") == "revised"
