from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class IncomingMessage(BaseModel):
    """Canonical representation of an incoming message from any channel."""
    user_id: str = Field(..., description="Unique identifier (e.g., phone number)")
    channel: Literal["whatsapp", "messenger", "sms"]
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_path: Optional[str] = None
    user_name: Optional[str] = None

class OutboundMessage(BaseModel):
    """Canonical representation of an outbound message."""
    user_id: str
    text: str
    media_urls: List[str] = []
    quick_replies: List[str] = []
