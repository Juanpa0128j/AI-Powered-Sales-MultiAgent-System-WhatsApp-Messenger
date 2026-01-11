import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
import app.main

# NOTE: Decorators apply Top-Down to arguments.
# @patch(A) -> arg1
# @patch(B) -> arg2

# Corrected Test with proper Patch Order
@patch("app.main.agent_graph") # First Arg
@patch("app.main.whatsapp_client.send_message") # Second Arg
def test_full_sales_flow(mock_send_message, mock_agent_graph, client):
    # Configure AsyncMock for ainvoke
    mock_agent_graph.ainvoke = AsyncMock()
    mock_agent_graph.ainvoke.return_value = {
        "messages": [MagicMock(content="We have running shoes.")]
    }
    
    # Bridge Payload
    payload = {
        "from": "123@c.us",
        "body": "Do you have shoes?",
    }
    
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 200
    # Normalized ID check
    mock_send_message.assert_called_with(to="whatsapp:+123", body="We have running shoes.")

@patch("app.main.whatsapp_client.send_message")
@patch("app.main.agent_graph") # Mock graph to prevent real calls if System Guard fails
def test_admin_commands_and_handoff(mock_graph, mock_send_message, client):
    # 1. Admin sends /stop
    client.post("/webhook", json={"from": "ADMIN@c.us", "body": "/stop"})
    mock_send_message.assert_called_with("whatsapp:+ADMIN", "⛔ SISTEMA DETENIDO (Global Kill Switch Activado).")
    
    # 2. User tries to chat -> "halted"
    # Reset mock to capture new calls clearly
    mock_send_message.reset_mock()
    client.post("/webhook", json={"from": "CLIENT@c.us", "body": "Hello"})
    
    # Ensure graph was NOT called
    mock_graph.ainvoke.assert_not_called()
    
    # 3. Admin sends /start
    client.post("/webhook", json={"from": "ADMIN@c.us", "body": "/start"})
    
    # 4. User tries again -> "ok"
    # Configure mock for the success case
    mock_graph.ainvoke = AsyncMock()
    mock_graph.ainvoke.return_value = {"messages": [MagicMock(content="Hi")]}
    
    response = client.post("/webhook", json={"from": "CLIENT@c.us", "body": "Hello"})
    assert response.json()["status"] == "ok"
    mock_graph.ainvoke.assert_called_once()

def test_rate_limiter(client):
    from app.main import limiter
    user = "whatsapp:+123" # Matches 123@c.us normalization
    limiter.usage = {} # Reset
    
    # Send 50 messages
    for _ in range(50):
        limiter.check_and_increment(user)
        
    # 51st message should fail
    # We need to mock Client again to avoid errors printing to stdout/real net calls
    # Also patch agent_graph to ensure we don't hit it (and confirm the bug if we do)
    with patch("app.main.whatsapp_client.send_message"), \
         patch("app.main.agent_graph") as mock_graph:
        
        response = client.post("/webhook", json={"from": "123@c.us", "body": "Spam"}) # from -> 123@c.us maps to whatsapp:+123
        
        # If this fails, it means we hit the graph!
        mock_graph.ainvoke.assert_not_called()
        assert response.json()["status"] == "rate_limit_exceeded"
