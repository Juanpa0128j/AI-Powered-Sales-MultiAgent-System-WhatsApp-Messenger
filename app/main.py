from fastapi import FastAPI, Request
from app.gateways.http_adapter import parse_bridge_webhook
from app.gateways.bridge_client import WhatsAppBridgeClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Agentic Sales System (WhatsApp Web)")
whatsapp_client = WhatsAppBridgeClient()

@app.get("/")
async def root():
    return {"status": "alive", "message": "Agentic Sales System (Bridge Mode)"}

from app.agent.graph import create_graph
from langchain_core.messages import HumanMessage

from app.utils.rate_limiter import RateLimiter
from app.utils.logger import app_logger

# Initialize Graph
agent_graph = create_graph()
# Global Rate Limiter (50 msgs/day per user)
limiter = RateLimiter(daily_limit=50)

# Global Safety Switch
SYSTEM_ACTIVE = True

@app.on_event("startup")
async def startup_event():
    app_logger.info("🚀 Agentic Sales System STARTED.")

@app.post("/webhook")
async def webhook(request: Request):
    global SYSTEM_ACTIVE
    
    # 1. Parse & Normalize (Changed to Bridge Parser)
    try:
        incoming_msg = await parse_bridge_webhook(request)
    except Exception as e:
        app_logger.error(f"Failed to parse webhook: {e}")
        return {"status": "error", "reason": str(e)}

    text = incoming_msg.text.strip()
    user_id = incoming_msg.user_id
    
    app_logger.info(f"📩 Webhook received from {user_id}: {text[:50]}...")
    
    if incoming_msg.media_path:
        app_logger.info(f"📷 Media received at: {incoming_msg.media_path}")
    
    # --- RATE LIMIT CHECK ---
    # Only limit users, not admin commands (commands start with /)
    if not text.startswith("/") and not limiter.check_and_increment(user_id):
        app_logger.warning(f"⛔ Rate limit exceeded for {user_id}")
        # Send via Bridge
        whatsapp_client.send_message(user_id, "⚠️ Límite diario de mensajes alcanzado. Por favor, contacte a un humano si requiere asistencia urgente.")
        return {"status": "rate_limit_exceeded"}

    # 2. Config for Persistence (Thread ID = User Phone)
    config = {"configurable": {"thread_id": user_id}}
    
    # --- ADMIN COMMANDS (Intercept before Graph) ---
    if text.startswith("/"):
        command = text.lower()
        app_logger.info(f"🔧 Admin Command executing: {command} by {user_id}")
        
        if command == "/status":
            status = "🟢 ONLINE" if SYSTEM_ACTIVE else "🔴 OFFLINE"
            # Try to get thread state
            try:
                state = await agent_graph.aget_state(config)
                thread_status = "🔇 MUTED" if state.values.get("handoff_active") else "🔊 ACTIVE"
            except:
                thread_status = "🆕 NEW"
            
            whatsapp_client.send_message(user_id, f"System: {status}\nThread: {thread_status}")
            return {"status": "command_executed"}

        if command == "/stop": # Global Panic Switch
            SYSTEM_ACTIVE = False
            app_logger.critical("🛑 SYSTEM HALTED BY ADMIN")
            whatsapp_client.send_message(user_id, "⛔ SISTEMA DETENIDO (Global Kill Switch Activado).")
            return {"status": "system_stopped"}
            
        if command == "/start": # Global Resume
            SYSTEM_ACTIVE = True
            app_logger.info("✅ SYSTEM RESUMED BY ADMIN")
            whatsapp_client.send_message(user_id, "✅ SISTEMA REANUDADO.")
            return {"status": "system_started"}
            
        if command in ["/mute", "/deactivate"]: # User Specific Handoff (Manual)
            await agent_graph.aupdate_state(config, {"handoff_active": True})
            app_logger.info(f"🔇 Handoff ACTIVATED for {user_id}")
            whatsapp_client.send_message(user_id, "🔇 Agente silenciado. Control humano activo.")
            return {"status": "thread_muted"}
            
        if command in ["/unmute", "/activate"]: # User Specific Resume
            await agent_graph.aupdate_state(config, {"handoff_active": False})
            app_logger.info(f"🔊 Handoff DEACTIVATED for {user_id}")
            whatsapp_client.send_message(user_id, "🔊 Agente REACTIVADO para este chat.")
            return {"status": "thread_unmuted"}

        # Catch-all for unknown commands to prevent them going to the LLM
        whatsapp_client.send_message(user_id, f"⚠️ Comando desconocido: {command}")
        return {"status": "unknown_command"}
            
    # --- GLOBAL SAFETY CHECK ---
    if not SYSTEM_ACTIVE:
        app_logger.warning(f"🛑 System halted. Ignoring message from {user_id}")
        return {"status": "halted"}

    # --- CHECK THREAD STATE (Default: Muted) ---
    try:
        state = await agent_graph.aget_state(config)
        handoff_active = state.values.get("handoff_active")
        
        # If State is Empty (New Thread) OR handoff_active is None -> Default to TRUE (Muted)
        if not state.values or handoff_active is None:
             app_logger.info(f"🆕 New Thread/User {user_id}. Defaulting to MUTED (Deactivated).")
             # Initialize state as Muted
             await agent_graph.aupdate_state(config, {"handoff_active": True})
             # We do NOT return here, we let the check below catch it.
             handoff_active = True
        
        if handoff_active:
             app_logger.info(f"🔇 Ignored message from {user_id} (Agent Muted)")
             return {"status": "ignored_muted"}
             
    except Exception as e:
        app_logger.info(f"🆕 Error reading state (assuming new thread): {e}. Defaulting to MUTED.")
        # Attempt to init state
        await agent_graph.aupdate_state(config, {"handoff_active": True})
        return {"status": "ignored_muted"}
            
    # --- GLOBAL SAFETY CHECK ---
    if not SYSTEM_ACTIVE:
        app_logger.warning(f"🛑 System halted. Ignoring message from {user_id}")
        return {"status": "halted"}

    # 3. Invoke Agent
    # Define generic state input
    input_state = {
        "messages": [HumanMessage(content=incoming_msg.text)],
        "user_id": user_id,
        "channel": incoming_msg.channel
    }
    
    # Run the graph!
    try:
        final_output = await agent_graph.ainvoke(input_state, config=config)
    except Exception as e:
        app_logger.error(f"❌ Error invoking agent: {e}", exc_info=True)
        whatsapp_client.send_message(user_id, "⚠️ Error procesando solicitud.")
        return {"status": "error"}
    
    # 4. Extract Response
    last_message = final_output["messages"][-1]
    response_text = last_message.content
    
    app_logger.info(f"📤 Sending response to {user_id}: {response_text[:50]}...")

    # 5. Handle Media (Check if tool output had media - Simplify for now)
    # Ideally, we check if the last tool message had an artifact or if the AI text contains a URL.
    # For now, we just send the text response.
    
    whatsapp_client.send_message(
        to=incoming_msg.user_id,
        body=response_text
    )
    
    return {"status": "ok"}
