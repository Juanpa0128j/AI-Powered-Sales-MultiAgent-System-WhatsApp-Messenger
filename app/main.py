from fastapi import FastAPI, Request
from app.gateways.http_adapter import parse_bridge_webhook
from app.gateways.bridge_client import WhatsAppBridgeClient
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    app_logger.info("🚀 Agentic Sales System STARTED.")
    
    # Clean up old media files (TTL: 6h) on startup
    from app.utils.media_processor import cleanup_old_files
    import os
    media_dir = os.path.join(os.getcwd(), "whatsapp-gateway", "media")
    cleanup_old_files(media_dir, max_age_hours=6)
    
    # --- Periodic Cleanup Task ---
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(60 * 60)  # every hour
            cleanup_old_files(media_dir, max_age_hours=6)
            app_logger.info("🧹 Periodic media cleanup executed.")
    
    # Start background task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    app.state.cleanup_task = cleanup_task
    
    yield
    # --- Shutdown Logic ---
    app_logger.info("🛑 Agentic Sales System STOPPING.")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Agentic Sales System (WhatsApp Web)", lifespan=lifespan)
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

# Global Safety Switch (Default: False/Offline for safety)
SYSTEM_ACTIVE = False
# Global Mute Switch (Default: True/All users muted by default)
GLOBAL_MUTE_ALL = True

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
    
    # --- MEDIA HANDLING (Audio Transcription) ---
    if incoming_msg.media_path:
        app_logger.info(f"📷 Media received at: {incoming_msg.media_path}")
        
        # Check if it's audio (WhatsApp usually uses .oga or .mp3)
        if incoming_msg.media_path.endswith((".oga", ".mp3", ".wav", ".m4a")):
            from app.utils.media_processor import transcribe_audio, cleanup_file
            
            # Transcribe
            transcription = transcribe_audio(incoming_msg.media_path)
            
            # Update text with transcription
            if transcription:
                text = f"[Audio Transcrito]: {transcription}"
                app_logger.info(f"🗣️ User sent Audio: {text}")
            
            # Cleanup immediately (TTL = 0 for processed audio)
            cleanup_file(incoming_msg.media_path)
            
    # --- CONTEXT HANDLING (Quoted Messages) ---
    if incoming_msg.quoted_text:
        app_logger.info(f"💬 Quoted Message found: {incoming_msg.quoted_text[:50]}...")
        # Prepend context to the user's message so the LLM knows what they are replying to
        text = f"[Respondiendo a: \"{incoming_msg.quoted_text}\"] {text}"
    
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
        import os
        # Load authorized admin number from Env
        # Normalized format: 1234567890@c.us
        # User defined ADMIN_WHATSAPP_NUMBER in .env is usually with whatsapp:+ or plain.
        # We need to normalize it or allow raw.
        admin_number = os.getenv("ADMIN_WHATSAPP_NUMBER", "").replace("whatsapp:+", "").strip()
        
        # Check Authorization
        # We check if user_id (e.g., 57314...@c.us) contains the admin number.
        if admin_number not in user_id:
             app_logger.warning(f"⚠️ UNAUTHORIZED COMMAND ATTEMPT from {user_id}: {text}")
             # Silent ignore
             return {"status": "unauthorized"}

        command_parts = text.split(" ") # Split command and args
        command = command_parts[0].lower()
        target_id = user_id # Default to self

        # Handle Target Argument: /mute @123456 or /mute 123456
        if len(command_parts) > 1:
            raw_target = command_parts[1].strip()
            # Basic normalization to append @c.us if missing and numeric
            if "@" not in raw_target:
                target_id = f"{raw_target}@c.us"
            else:
                target_id = raw_target
        
        app_logger.info(f"🔧 Admin Command executing: {command} on target {target_id} by {user_id}")
        
        # Config for TARGET thread
        target_config = {"configurable": {"thread_id": target_id}}

        if command == "/mute-all":
            GLOBAL_MUTE_ALL = True
            app_logger.info("🔇 GLOBAL MUTE ACTIVATED (All users muted by default).")
            whatsapp_client.send_message(user_id, "🔇 MUTE GLOBAL ACTIVADO.\nTodos los usuarios nuevos estarán silenciados por defecto.")
            return {"status": "global_mute_on"}

        if command == "/unmute-all":
            GLOBAL_MUTE_ALL = False
            app_logger.info("🔊 GLOBAL MUTE DEACTIVATED (Users active by default).")
            whatsapp_client.send_message(user_id, "🔊 MUTE GLOBAL DESACTIVADO.\nLos usuarios nuevos serán atendidos por la IA.")
            return {"status": "global_mute_off"}

        if command == "/help":
            help_text = (
                "🤖 *Admin Command List:*\n\n"
                "✅ `/start` - Resume system globally.\n"
                "⛔ `/stop` - Halt system globally (Kill Switch).\n"
                "🔇 `/mute-all` - Auto-mute ALL new conversations (Default).\n"
                "🔊`/unmute-all` - Auto-unmute ALL new conversations.\n"
                "📊 `/status [target]` - Check system & thread status.\n"
                "🔇 `/mute [target]` - Deactivate AI for a user.\n"
                "🔊 `/unmute [target]` - Activate AI for a user.\n"
                "ℹ️ `/help` - Show this menu."
            )
            whatsapp_client.send_message(user_id, help_text)
            return {"status": "command_executed"}

        if command == "/status":
            # Handle "all" case
            if len(command_parts) > 1 and command_parts[1].lower() == "all":
                 if not hasattr(agent_graph.checkpointer, "storage"):
                     whatsapp_client.send_message(user_id, "⚠️ Storage listing not supported with current Checkpointer.")
                     return {"status": "error"}
                 
                 # Extract unique thread_ids from MemorySaver storage
                 # MemorySaver storage keys are (thread_id, checkpoint_id)
                 unique_threads = set()
                 for key in agent_graph.checkpointer.storage.keys():
                     if isinstance(key, tuple) and len(key) >= 1:
                         unique_threads.add(key[0])
                 
                 report = "📊 *User Status Report:*\n"
                 for tid in unique_threads:
                     try:
                         # Get latest state for thread
                         t_state = await agent_graph.aget_state({"configurable": {"thread_id": tid}})
                         t_status = "🔇 MUTED" if t_state.values.get("handoff_active") else "🔊 ACTIVE"
                         report += f"\n- {tid}: {t_status}"
                     except Exception:
                         report += f"\n- {tid}: ❓ Unknown"
                 
                 if not unique_threads:
                     report += "\n(No active sessions found)"
                 
                 whatsapp_client.send_message(user_id, report)
                 return {"status": "report_generated"}

            # Standard Status
            status = "🟢 ONLINE" if SYSTEM_ACTIVE else "🔴 OFFLINE"
            mute_mode = "🔇 MUTED BY DEFAULT" if GLOBAL_MUTE_ALL else "🔊 ACTIVE BY DEFAULT"
            
            # Try to get thread state
            try:
                state = await agent_graph.aget_state(target_config)
                thread_status = "🔇 MUTED" if state.values.get("handoff_active") else "🔊 ACTIVE"
            except:
                thread_status = "🆕 NEW/EMPTY"
            
            whatsapp_client.send_message(user_id, f"System: {status}\nMode: {mute_mode}\nTarget ({target_id}): {thread_status}")
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
            await agent_graph.aupdate_state(target_config, {"handoff_active": True}, as_node="admin")
            app_logger.info(f"🔇 Handoff ACTIVATED for {target_id}")
            whatsapp_client.send_message(user_id, f"🔇 Agente silenciado para {target_id}.")
            return {"status": "thread_muted"}
            
        if command in ["/unmute", "/activate"]: # User Specific Resume
            await agent_graph.aupdate_state(target_config, {"handoff_active": False}, as_node="admin")
            app_logger.info(f"🔊 Handoff DEACTIVATED for {target_id}")
            whatsapp_client.send_message(user_id, f"🔊 Agente REACTIVADO para {target_id}.")
            return {"status": "thread_unmuted"}

        # Catch-all for unknown commands to prevent them going to the LLM
        whatsapp_client.send_message(user_id, f"⚠️ Comando desconocido: {command}")
        return {"status": "unknown_command"}
            
    # --- GLOBAL SAFETY CHECK ---
    if not SYSTEM_ACTIVE:
        app_logger.warning(f"🛑 System halted. Ignoring message from {user_id}")
        return {"status": "halted"}

    # --- CHECK THREAD STATE (Default: Depends on GLOBAL_MUTE_ALL) ---
    try:
        state = await agent_graph.aget_state(config)
        handoff_active = state.values.get("handoff_active")
        
        # If State is Empty (New Thread) OR handoff_active is None -> Default to GLOBAL_MUTE_ALL
        if not state.values or handoff_active is None:
             default_state = GLOBAL_MUTE_ALL
             status_msg = "MUTED" if default_state else "ACTIVE"
             app_logger.info(f"🆕 New Thread/User {user_id}. Defaulting to {status_msg} (Global Config).")
             
             # Initialize state
             await agent_graph.aupdate_state(config, {"handoff_active": default_state}, as_node="admin")
             # We do NOT return here, we let the check below catch it.
             handoff_active = default_state
        
        if handoff_active:
             app_logger.info(f"🔇 Ignored message from {user_id} (Agent Muted)")
             return {"status": "ignored_muted"}
             
    except Exception as e:
        app_logger.info(f"🆕 Error reading state (assuming new thread): {e}. Defaulting to GLOBAL_MUTE_ALL.")
        # Attempt to init state to GLOBAL_MUTE_ALL
        await agent_graph.aupdate_state(config, {"handoff_active": GLOBAL_MUTE_ALL}, as_node="admin")
        
        if GLOBAL_MUTE_ALL:
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

    # 5. Handle Media (Check if tool output had media)
    from langchain_core.messages import ToolMessage
    import json
    
    media_url = None
    
    # Scan recent messages for media artifacts from tools
    # We look efficiently at the last few messages
    for msg in reversed(final_output["messages"]):
        if isinstance(msg, ToolMessage) and msg.name == "get_product_media":
            try:
                # Content might be a dict or stringified dict
                content = msg.content
                if isinstance(content, str):
                    # Python dict string to JSON approximation (or use ast.literal_eval for safety)
                    # Simple replace for ' to " might fail on text but ok for simple URLs
                    if "'" in content and '"' not in content:
                        content = content.replace("'", '"')
                    content = json.loads(content)
                
                if isinstance(content, dict) and "url" in content:
                    media_url = content["url"]
                    app_logger.info(f"🖼️ Found Image URL to send: {media_url}")
                    break
            except Exception as e:
                app_logger.warning(f"Failed to parse media tool output: {e}")

    whatsapp_client.send_message(
        to=incoming_msg.user_id,
        body=response_text,
        media_url=media_url
    )
    
    return {"status": "ok"}
