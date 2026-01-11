import pytest
from unittest.mock import patch, MagicMock, AsyncMock # Added AsyncMock/MagicMock imports for consistency
from app.main import app
from app.gateways.http_adapter import parse_bridge_webhook
from fastapi import Request

# --- Unit Tests for Normalization ---

@pytest.mark.asyncio
async def test_parse_whatsapp_message():
    # Helper unit test (logic only)
    pass

# --- Integration Tests for Webhook Endpoint ---

@patch("app.main.agent_graph")
@patch("app.main.whatsapp_client")
def test_webhook_bridge_json(mock_bridge_client, mock_graph, client):
    # Setup mock
    mock_bridge_client.send_message.return_value = "MSG_ID_123"
    
    # Mock Graph Response
    mock_graph.ainvoke = AsyncMock()
    mock_graph.ainvoke.return_value = {
        "messages": [MagicMock(content="Bridge Response")]
    }
    
    # Mock State (needed for Default Muted check)
    mock_state = MagicMock()
    mock_state.values = {"handoff_active": False} # Active by default
    mock_graph.aget_state = AsyncMock(return_value=mock_state)
    mock_graph.aupdate_state = AsyncMock()
    
    # New Bridge JSON Payload
    payload = {
        "from": "1234567890@c.us",
        "body": "Hello Bridge",
        "hasMedia": False
    }
    
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 200
    mock_bridge_client.send_message.assert_called_once()
    
    # Verify we got the agent response
    call_args = mock_bridge_client.send_message.call_args
    # call_args[0] = args tuple, call_args[1] = kwargs
    # Bridge Client signature: send_message(to, body) -> Positional or Keyword?
    # used in main: whatsapp_client.send_message(user_id, body) -> Positional usually if not specified
    # Let's check main.py usage: 
    # whatsapp_client.send_message(to=incoming_msg.user_id, body=response_text) -> Keyword
    
    # Verify arguments
    _, kwargs = call_args
    assert kwargs["to"] == "1234567890@c.us" # Unchanged ID
    assert "Bridge Response" in kwargs["body"]
