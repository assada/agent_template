import json
import tracemalloc
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk
from langfuse._client.span import LangfuseSpan

from app.agent.models import HumanMessage
from app.agent.services.events import EndEvent, TokenEvent
from app.agent.services.events.base_event import BaseEvent
from app.agent.services.stream_processor import StreamProcessor

tracemalloc.start()


@pytest.fixture
def stream_processor():
    return StreamProcessor()


@pytest.fixture
def mock_run_id():
    return uuid4()


@pytest.fixture
def mock_span():
    span = Mock(spec=LangfuseSpan)
    span.trace_id = "test_trace_id"
    span.update = Mock()
    return span


class TestStreamProcessor:
    def test_create_ai_message_with_valid_keys(self, stream_processor):
        parts = {
            "content": "test content",
            "id": "test_id",
            "invalid_key": "should_be_filtered",
        }

        result = stream_processor._create_ai_message(parts)

        assert isinstance(result, AIMessage)
        assert result.content == "test content"
        assert not hasattr(result, "invalid_key")

    def test_create_ai_message_empty_parts(self, stream_processor):
        result = stream_processor._create_ai_message({"content": ""})
        assert isinstance(result, AIMessage)
        assert result.content == ""

    def test_flatten_updates_with_messages(self, stream_processor):
        updates = {
            "node1": {"messages": ["msg1", "msg2"]},
            "node2": {"messages": ["msg3"]},
            "node3": None,
        }

        result = stream_processor._flatten_updates(updates)

        assert result == ["msg1", "msg2", "msg3"]

    def test_flatten_updates_empty(self, stream_processor):
        result = stream_processor._flatten_updates({})
        assert result == []

    def test_wrap_as_list(self, stream_processor):
        event = "test_event"
        result = stream_processor._wrap_as_list(event)
        assert result == ["test_event"]

    @patch("app.agent.services.stream_processor.to_chat_message")
    def test_messages_to_events_with_tuple_messages(
        self, mock_to_chat_message, stream_processor, mock_run_id, mock_span
    ):
        mock_chat = Mock()
        mock_chat.type = "ai_message"
        mock_chat.model_dump.return_value = {"content": "test"}
        mock_to_chat_message.return_value = mock_chat

        messages = [("content", "test content"), ("id", "test_id"), Mock()]

        with patch.object(BaseEvent, "from_payload") as mock_from_payload:
            mock_from_payload.return_value = Mock()
            result = stream_processor._messages_to_events(
                messages, mock_run_id, mock_span
            )

            assert len(result) >= 1
            mock_from_payload.assert_called()

    @patch("app.agent.services.stream_processor.to_chat_message")
    def test_messages_to_events_with_human_message_skip(
        self, mock_to_chat_message, stream_processor, mock_run_id
    ):
        human_msg = Mock(spec=HumanMessage)
        human_msg.content = "test content"
        mock_to_chat_message.return_value = human_msg

        message = Mock()
        message.content = "test content"

        result = stream_processor._messages_to_events([message], mock_run_id, None)

        assert result == []

    @patch("app.agent.services.stream_processor.strip_tool_calls")
    @patch("app.agent.services.stream_processor.concat_text")
    def test_token_event_success(
        self, mock_concat_text, mock_strip_tool_calls, stream_processor, mock_run_id
    ):
        mock_strip_tool_calls.return_value = "cleaned content"
        mock_concat_text.return_value = "concatenated content"

        msg = Mock(spec=AIMessageChunk)
        msg.content = "test content"
        metadata = {"tags": []}
        event = (msg, metadata)

        result = stream_processor._token_event(event, mock_run_id)

        assert isinstance(result, TokenEvent)
        mock_strip_tool_calls.assert_called_once_with("test content")
        mock_concat_text.assert_called_once_with("cleaned content")

    @pytest.mark.asyncio
    async def test_process_stream_updates_mode(
        self, stream_processor, mock_run_id, mock_span
    ):
        async def mock_stream():
            yield ("updates", {"node1": {"messages": ["test_msg"]}})

        with patch.object(
            stream_processor, "_messages_to_events"
        ) as mock_messages_to_events:
            mock_event = Mock()
            mock_messages_to_events.return_value = [mock_event]

            events = []
            async for event in stream_processor.process_stream(
                mock_stream(), mock_run_id, mock_span
            ):
                events.append(event)

            assert len(events) == 2
            assert events[0] == mock_event
            assert isinstance(events[1], EndEvent)
            mock_span.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_stream_custom_mode(self, stream_processor, mock_run_id):
        async def mock_stream():
            yield ("custom", "test_payload")

        with patch.object(
            stream_processor, "_messages_to_events"
        ) as mock_messages_to_events:
            mock_event = Mock()
            mock_messages_to_events.return_value = [mock_event]

            events = []
            async for event in stream_processor.process_stream(
                mock_stream(), mock_run_id
            ):
                events.append(event)

            assert len(events) == 2
            assert events[0] == mock_event
            assert isinstance(events[1], EndEvent)

    @pytest.mark.asyncio
    async def test_process_stream_messages_mode(self, stream_processor, mock_run_id):
        mock_token = Mock(spec=TokenEvent)

        async def mock_stream():
            yield ("messages", ("test_msg", {}))

        with patch.object(stream_processor, "_token_event") as mock_token_event:
            mock_token_event.return_value = mock_token

            events = []
            async for event in stream_processor.process_stream(
                mock_stream(), mock_run_id
            ):
                events.append(event)

            assert len(events) == 2
            assert events[0] == mock_token
            assert isinstance(events[1], EndEvent)

    @pytest.mark.asyncio
    async def test_process_stream_end_event_format(self, stream_processor, mock_run_id):
        async def mock_stream():
            return
            yield  # unreachable

        events = []
        async for event in stream_processor.process_stream(mock_stream(), mock_run_id):
            events.append(event)

        assert len(events) == 1
        end_event = events[0]
        assert isinstance(end_event, EndEvent)

        data = json.loads(end_event.data)
        assert data["run_id"] == str(mock_run_id)
        assert data["status"] == "completed"
