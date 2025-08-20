from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from pydantic import BaseModel, Field


class BaseState(BaseModel):
    messages: Annotated[Sequence[AnyMessage], add_messages] = Field(
        default_factory=list
    )
    llm_context: list[AnyMessage] | None = Field(default=None, exclude=True)
    message_trace_map: list[dict[str, str | None]] = Field(default_factory=list)


class State(BaseState):
    is_last_step: IsLastStep = Field(default=False)

    # retrieved_documents: List[Document] = field(default_factory=list)
    # extracted_entities: Dict[str, Any] = field(default_factory=dict)
    # api_connections: Dict[str, Any] = field(default_factory=dict)
