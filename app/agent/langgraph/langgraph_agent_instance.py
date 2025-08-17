from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langgraph.graph.state import CompiledStateGraph

from app.agent.interfaces import AgentInstance
from app.agent.langgraph.utils import to_chat_message
from app.agent.services.events import EndEvent, ErrorEvent
from app.agent.services.events.base_event import BaseEvent
from app.agent.services.stream_processor import StreamProcessor
from app.bootstrap.config import AppConfig
from app.models import Thread, User
from app.models.thread import ThreadStatus

logger = logging.getLogger(__name__)


class LangGraphAgentInstance(AgentInstance):
    def __init__(
            self,
            agent_id: str,
            graph: CompiledStateGraph[Any, Any, Any],
            tracing_client: Langfuse,
            config: AppConfig | None = None,
    ):
        super().__init__(agent_id, config or AppConfig())
        self.graph = graph
        self._tracing_client = tracing_client
        self.stream_processor = StreamProcessor()

    async def stream_response(  # type: ignore[override]
            self, message: str, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        with self._tracing_client.start_as_current_span(
                name=self.graph.name, input=message
        ) as span:
            run_id = uuid4()

            thread.status = ThreadStatus.busy
            thread.updated_at = datetime.now(UTC)

            inputs = {
                "messages": [HumanMessage(content=message)],
            }

            config = RunnableConfig(
                configurable={
                    "thread_id": thread.id,
                    "user_id": user.id,
                },
                metadata={
                    "langfuse_session_id": str(thread.id),
                    "langfuse_user_id": str(user.id),
                    "langfuse_tags": ["production", "chat-bot"],
                    "trace_id": span.trace_id,
                },
                run_id=run_id,
                callbacks=[CallbackHandler()],
            )

            try:
                yield BaseEvent.from_payload(
                    event="thread",
                    payload={
                        "id": str(thread.id),
                        "agent_id": thread.agent_id,
                        "user_id": str(user.id),
                        "status": thread.status.value if thread.status else None,
                    },
                    source="stream",
                ).model_dump()

                stream = self.graph.astream(
                    inputs, stream_mode=["updates", "messages", "custom"], config=config
                )
                async for event in self.stream_processor.process_stream(
                        stream,  # type: ignore[arg-type]
                        run_id,
                        span,
                ):
                    thread.status = ThreadStatus.idle
                    yield event.model_dump()
            except Exception as e:
                thread.status = ThreadStatus.error
                yield ErrorEvent(
                    data=json.dumps({"run_id": str(run_id), "content": str(e)})
                ).model_dump()

    async def load_history(  # type: ignore[override]
            self, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        try:
            state_snapshot = await self.graph.aget_state(
                config=RunnableConfig(
                    configurable={"thread_id": thread.id, "user_id": user.id}
                ),
            )

            trace_by_id = {
                m["id"]: m["trace_id"]
                for m in state_snapshot.values.get("message_trace_map", [])
            }

            messages = state_snapshot.values.get("messages", [])
            if not messages:
                yield EndEvent(data=json.dumps({"status": "completed"})).model_dump()
                return

            for m in messages:
                chat_msg = to_chat_message(m, trace_id=trace_by_id.get(m.id))

                event = BaseEvent.from_payload(
                    event=chat_msg.type, payload=chat_msg.model_dump(), source="history"
                )

                yield event.model_dump()

            yield EndEvent(data=json.dumps({"status": "completed"})).model_dump()

        except Exception as e:
            logger.error(f"Error loading history: {e}")
            yield ErrorEvent(
                data=json.dumps({"content": f"Error loading history: {str(e)}"})
            ).model_dump()
