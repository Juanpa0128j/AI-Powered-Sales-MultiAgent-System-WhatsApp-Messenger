from pydantic import BaseModel, Field
from fastapi import Request
from app.gateways.schemas import IncomingMessage

class BridgePayload(BaseModel):
    from_: str = Field(alias="from")
    body: str
    hasMedia: bool = False

async def parse_bridge_webhook(request: Request) -> IncomingMessage:
    """
    Parses JSON payload from local WhatsApp Bridge (whatsapp-web.js).
    """
    data = await request.json()
    
    # Normalize ID: "123456789@c.us" OR "123456789@g.us"
    # We MUST preserve the suffix (@c.us or @g.us) to know if it's a user or group.
    # We will PREPEND "whatsapp:" to keep internal consistency if needed, but 
    # since we are moving away from Twilio, we could just use the raw ID.
    # However, to be safe with existing agent logic that might expect strings, 
    # let's just use the raw ID from the Bridge.
    user_id = data.get("from", "")
    
    # Create standardized IncomingMessage
    # We use the full ID (e.g. "12345@c.us") as the user_id.
    normalized_user_id = user_id
    
    return IncomingMessage(
        text=data.get("body", ""),
        user_id=normalized_user_id,
        channel="whatsapp", # Always whatsapp for this bridge
        media_path=data.get("mediaPath"),
        raw_payload=data
    )
