from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 

from app.agent.state import SalesState
from app.agent.nodes import chatbot_node, scan_notification_node, tools

def route_start(state):
    """Check if we are in handoff mode"""
    if state.get("handoff_active"):
        return END
    return "chatbot"

def create_graph():
    workflow = StateGraph(SalesState)
    
    # Add Nodes
    workflow.add_node("chatbot", chatbot_node)
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)
    workflow.add_node("scanner", scan_notification_node)
    
    # Edges
    # 1. Start -> Check Handoff -> Chatbot OR End
    workflow.add_conditional_edges(START, route_start)
    
    # 2. Chatbot -> Tools OR End
    workflow.add_conditional_edges("chatbot", tools_condition)
    
    # 3. Tools -> Scanner (Check if we should silence) -> Chatbot
    workflow.add_edge("tools", "scanner")
    workflow.add_edge("scanner", "chatbot")
    
    checkpointer = MemorySaver()
    app_graph = workflow.compile(checkpointer=checkpointer)
    
    return app_graph
