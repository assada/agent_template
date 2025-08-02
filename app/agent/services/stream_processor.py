from __future__ import annotations

import inspect
import json
import logging
from collections.abc import AsyncGenerator, Callable, Iterable
from enum import Enum
from typing import Any
from uuid import UUID

from langchain_core.messages import AIMessage, AIMessageChunk
from langfuse._client.span import LangfuseSpan

from app.agent.langgraph.utils import (
    concat_text,
    strip_tool_calls,
    to_chat_message,
)
from app.agent.models import AIMessage as CustomAIMessage
from app.agent.models import HumanMessage, Token
from app.agent.services.events import EndEvent, ErrorEvent, TokenEvent
from app.agent.services.events.base_event import BaseEvent

logger = logging.getLogger(__name__)


class StreamMode(str, Enum):
    UPDATES = "updates"
    CUSTOM = "custom"
    MESSAGES = "messages"


class StreamProcessor:
    _ai_signature = inspect.signature(AIMessage)
    _ai_valid_keys = set(_ai_signature.parameters)

    @staticmethod
    def _create_ai_message(parts: dict[str, Any]) -> AIMessage:
        filtered = {
            k: v for k, v in parts.items() if k in StreamProcessor._ai_valid_keys
        }
        return AIMessage(**filtered)

    @staticmethod
    def _flatten_updates(updates: dict[str, Any]) -> list[Any]:
        return [
            msg
            for node_updates in updates.values()
            for msg in (node_updates or {}).get("messages", [])
        ]

    @staticmethod
    def _wrap_as_list(event: Any) -> list[Any]:
        return [event]

    def _messages_to_events(
        self,
        messages: list[Any],
        run_id: UUID,
        span: LangfuseSpan | None,
    ) -> list[BaseEvent]:
        consolidated: list[Any] = []
        current: dict[str, Any] = {}

        for message in messages:
            if isinstance(message, tuple):
                key, value = message
                current[key] = value
                continue

            if current:
                consolidated.append(self._create_ai_message(current))
                current = {}

            consolidated.append(message)

        if current:
            consolidated.append(self._create_ai_message(current))

        events: list[BaseEvent] = []
        for message in consolidated:
            try:
                chat = to_chat_message(message)
                chat.run_id = str(run_id)

                if (
                    isinstance(chat, HumanMessage)
                    and getattr(message, "content", None) == chat.content
                ):
                    continue

                if span and isinstance(chat, CustomAIMessage):
                    chat.trace_id = span.trace_id

                events.append(
                    BaseEvent.from_payload(
                        event=chat.type,
                        payload=chat.model_dump(),
                        source="stream",
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to parse message: %s", exc)
                events.append(
                    ErrorEvent(data=json.dumps({"content": "Unexpected error"}))
                )

        return events

    @staticmethod
    def _token_event(
        event: tuple[AIMessageChunk, dict[str, Any]],
        run_id: UUID,
    ) -> TokenEvent | None:
        msg, metadata = event
        if not isinstance(msg, AIMessageChunk) or "skip_stream" in metadata.get(
            "tags", []
        ):
            return None

        content = strip_tool_calls(msg.content)
        if not content:
            return None

        token = Token(
            run_id=str(run_id),
            content=concat_text(content),
        )
        return TokenEvent(data=token.model_dump_json())

    async def process_stream(
        self,
        stream: AsyncGenerator[tuple[str, Any]],
        run_id: UUID,
        span: LangfuseSpan | None = None,
    ) -> AsyncGenerator[BaseEvent]:
        strategy: dict[StreamMode, Callable[[Any], Iterable[list[Any]]]] = {
            StreamMode.UPDATES: lambda payload: [self._flatten_updates(payload)],
            StreamMode.CUSTOM: lambda payload: [self._wrap_as_list(payload)],
            StreamMode.MESSAGES: lambda _: [],
        }

        async for mode_str, payload in stream:
            try:
                mode = StreamMode(mode_str)
            except ValueError:
                logger.warning("Unknown stream mode '%s' – skipping", mode_str)
                continue

            if mode is StreamMode.MESSAGES:
                token = self._token_event(payload, run_id)
                if token:
                    yield token
                continue

            for messages in strategy[mode](payload):
                if not messages:
                    continue

                events = self._messages_to_events(messages, run_id, span)
                if span:
                    span.update(output=messages)

                for evt in events:
                    yield evt

        yield EndEvent(data=json.dumps({"run_id": str(run_id), "status": "completed"}))
