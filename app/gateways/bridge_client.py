import os
import httpx
from typing import List, Optional
from app.utils.logger import app_logger

class WhatsAppBridgeClient:
    def __init__(self):
        # Default to localhost:3000 if not set
        self.gateway_url = os.getenv("WHATSAPP_GATEWAY_URL", "http://localhost:3000")
    
    def send_message(self, to: str, body: str, media_urls: List[str] = None):
        """
        Send a message via the local Node.js Bridge.
        """
        # "to" format: whatsapp:+123456789 -> 123456789@c.us is handled by the Bridge
        
        payload = {
            "to": to,
            "body": body
        }
        
        # Support single media URL for now (Bridge logic handles one 'mediaUrl')
        if media_urls and len(media_urls) > 0:
            payload["mediaUrl"] = media_urls[0]

        endpoint = f"{self.gateway_url}/send"
        
        try:
            # Synch call for now (or convert to async if we change main.py architecture)
            # Using httpx for better potential async later
            response = httpx.post(endpoint, json=payload, timeout=10.0)
            response.raise_for_status()
            app_logger.debug(f"Bridge Response: {response.text}")
            return response.json().get("chatId")
        except Exception as e:
            app_logger.error(f"Error sending message via Bridge to {to}: {e}")
            return None

    def send_typing_indicator(self, to: str):
        """
        Send a 'typing...' signal to the user.
        """
        endpoint = f"{self.gateway_url}/chat/typing"
        try:
            httpx.post(endpoint, json={"to": to}, timeout=2.0)
            app_logger.debug(f"✍️ Typing indicator sent to {to}")
        except Exception as e:
            # Non-blocking error
            app_logger.warning(f"Failed to send typing indicator: {e}")
