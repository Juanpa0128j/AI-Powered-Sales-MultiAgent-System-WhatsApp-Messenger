# LangGraph state definition placeholder
from typing import Annotated, List, Union
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage

class SalesState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    user_id: str
    channel: str
    current_product: str
    negotiation_stage: str
    # TTL and other metadata will be managed here
