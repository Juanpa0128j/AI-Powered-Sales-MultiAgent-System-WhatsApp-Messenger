from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from app.utils.logger import app_logger

# Import tools
from app.tools.product_tools import lookup_product_info, check_inventory, get_product_media
from app.tools.search_tools import web_search_product
from app.tools.notification_tools import notify_admin_whatsapp

# LLM Setup
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Tools List
tools = [
    lookup_product_info, 
    check_inventory, 
    get_product_media, 
    web_search_product, 
    notify_admin_whatsapp
]

# System System Prompt (Injected Logic)
SYSTEM_PROMPT = """Eres el Asistente de Ventas de 'tucompraonline'.
Tu objetivo es ayudar al cliente, resolver dudas y CERRAR LA VENTA de manera ágil.

**REGLAS DE RESPUESTA (IMPORTANTE):**

1. **PRECIOS Y SALUDO INICIAL**:
   Si el cliente pregunta por el precio, disponibilidad o es su primer mensaje mostrando interés, USA SIEMPRE ESTE FORMATO EXACTO (reemplazando <PRECIO> con el valor real consultado):
   
   "Hola, bienvenido(a) a tu compraonline. Tenemos pago contraentrega en Medellín y su área metropolitana. El valor <PRECIO>+el domi. ¿Donde está ubicado/a?"

2. **CONSULTA DE INFORMACIÓN**:
   - Usa `lookup_product_info` para averiguar el precio y stock antes de responder.
   - Si no encuentras el producto, pide más detalles amablemente.

3. **OTROS CASOS**:
   - Si pregunta por fotos, usa `get_product_media`.
   - Si pregunta detalles técnicos y no los tienes, usa `web_search_product` (pero sé breve).
   - Si el cliente confirma la compra ("Lo quiero", "Envialo"), usa `notify_admin_whatsapp`.

**GUARDRAILS (SEGURIDAD):**
- Tu ÚNICA función es vender productos de 'tucompraonline'.
- Si te preguntan por temas ajenos (política, religión, código, etc.), responde:
  "Lo siento, solo puedo asistirte con información sobre nuestros productos y tu compra."
- NO inventes precios. Si no lo sabes, búscalo. Si no está en la base de datos, di que verificarás con un asesor humano.
"""

def chatbot_node(state):
    messages = state["messages"]
    user_id = state.get("user_id", "unknown")
    
    # Ensure system prompt is first
    if not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))
    
    app_logger.info(f"🤖 Agent processing for user {user_id}")
    
    model_with_tools = llm.bind_tools(tools)
    response = model_with_tools.invoke(messages)
    
    if response.tool_calls:
        tool_names = [t['name'] for t in response.tool_calls]
        app_logger.info(f"🛠️ Agent selected tools: {tool_names}")
    
    return {"messages": [response]}

def scan_notification_node(state):
    """
    Checks if the last message was a tool call to 'notify_admin_whatsapp'.
    If so, sets handoff_active = True.
    """
    messages = state["messages"]
    last_message = messages[-1]
    user_id = state.get("user_id", "unknown")
    
    # We look for ToolMessage from the specific tool name
    # But here we are AFTER the tool execution (ToolNode adds ToolMessage).
    if hasattr(last_message, "name") and last_message.name == "notify_admin_whatsapp":
        app_logger.info(f"🚨 Sales Handoff Triggered for {user_id}")
        return {"handoff_active": True}
        
    return {}
