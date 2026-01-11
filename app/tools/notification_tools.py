import os
from langchain_core.tools import tool
from app.gateways.bridge_client import WhatsAppBridgeClient

@tool
def notify_admin_whatsapp(summary: str, customer_contact: str):
    """
    Use this tool ONLY when the client indicates a clear intention to close the sale 
    (e.g., 'I want to buy', 'I'm interested', 'How's the process to buy?') or explicit handover request.
    Sends a WhatsApp to the store owner.
    """
    client = WhatsAppBridgeClient()
    admin_number = os.getenv("ADMIN_PHONE_NUMBER", "whatsapp:+123456789")
    
    if not admin_number:
        return "Error: Admin number not configured."

    message = f"🔔 *CIERRE DE VENTA DETECTADO*\n\n📄 **Resumen**: {summary}\n👤 **Cliente**: {customer_contact}\n\n⚠️ *Acción Requerida*: Contactar al cliente para finalizar pago."
    
    # Send to Admin
    client.send_message(to=admin_number, body=message)
    
    return "Notificación enviada al administrador."
