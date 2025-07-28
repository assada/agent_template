from typing import Literal

from pydantic import Field

from .chat_message import ChatMessage


class CustomUIMessage(ChatMessage):
    type: Literal["ui"] = "ui"
    component: str = Field(
        description="Type of the UI component",
        examples=["weather_widget", "news_feed", "stock_ticker"],
    )
    id: str = Field(
        description="Unique identifier for the UI component",
        examples=["weather_widget_123"],
    )
    params: dict[str, str] = Field(
        description="Parameters for the UI component",
        examples=[{"location": "Kyiv", "date": "2023-10-01"}],
    )
