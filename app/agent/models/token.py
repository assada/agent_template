from pydantic import Field

from .chat_message import ChatMessage, MessageType


class Token(ChatMessage):
    type: MessageType = "token"
    content: str = Field(
        description="Token content",
        examples=["Hello"],
    )
