from pydantic import Field

from .chat_message import ChatMessage, MessageType


class HumanMessage(ChatMessage):
    type: MessageType = "human_message"
    content: str = Field(
        description="Message content",
        examples=["What is the weather like today?"],
    )
