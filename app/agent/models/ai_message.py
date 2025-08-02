from pydantic import Field

from .chat_message import ChatMessage, MessageType


class AIMessage(ChatMessage):
    type: MessageType = "ai_message"
    content: str = Field(
        description="Message content",
        examples=["In the morning, the sun rises in the east and sets in the west."],
    )
