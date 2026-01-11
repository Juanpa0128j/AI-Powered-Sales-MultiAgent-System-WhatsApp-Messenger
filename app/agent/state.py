# LangGraph state definition placeholder
from typing import Annotated, List, Literal, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class SalesState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    user_id: str
    channel: str
    handoff_active: bool # If True, Agent stays silent
    current_product: str
    negotiation_stage: str
    # TTL and other metadata will be managed here
