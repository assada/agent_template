import logging
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException
from langfuse import Langfuse  # type: ignore[attr-defined]
from sse_starlette.sse import EventSourceResponse

from app.agent.factory import AgentFactory
from app.agent.interfaces import AgentInstance
from app.agent.services import AgentService
from app.bootstrap.agent_registry import validate_agent_id
from app.bootstrap.config import AppConfig
from app.http.requests import FeedbackRequest
from app.models import Thread, User
from app.models.thread import ThreadStatus
from app.repositories import ThreadRepository, UserRepository

logger = logging.getLogger(__name__)


class ThreadController:
    def __init__(self, config: AppConfig):
        self.config = config
        self.langfuse_client = Langfuse(debug=False)
        self.agent_factory = AgentFactory(config, self.langfuse_client)
        self._agent_instances: dict[str, AgentInstance] = {}
        self._agent_service = AgentService(self.langfuse_client)

    async def _get_agent_instance(self, agent_id: str) -> AgentInstance:
        if agent_id in self._agent_instances:
            return self._agent_instances[agent_id]

        agent_instance = await self.agent_factory.create_agent(agent_id)

        self._agent_instances[agent_id] = agent_instance
        logger.debug(f"Created and cached agent instance: {agent_id}")

        return agent_instance

    async def stream(
        self,
        agent_id: str | None,
        query: dict[str, Any] | list[Any] | str | float | bool | None,
        thread_id: UUID | None,
        metadata: dict[str, Any] | None,
        user: User,
    ) -> EventSourceResponse:
        try:
            effective_agent_id = validate_agent_id(agent_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        if thread_id is None:
            from datetime import UTC, datetime
            from uuid import uuid4

            thread = Thread(
                id=str(uuid4()),
                user_id="1437ade37359488e95c0727a1cdf1786d24edce3",
                status=ThreadStatus.idle,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                agent_id=effective_agent_id,
                metadata=metadata or {},
            )
            thread = await ThreadRepository.create_thread(thread)
        else:
            thread = await ThreadRepository.get_thread_by_id(str(thread_id))
            if agent_id and thread.agent_id != effective_agent_id:
                thread.agent_id = effective_agent_id
                thread = await ThreadRepository.update_thread(thread)

        try:
            agent_instance = await self._get_agent_instance(thread.agent_id)
            logger.debug(f"Received chat request: {str(query)[:50]}...")

            return EventSourceResponse(
                agent_instance.stream_response(str(query), thread, user),  # type: ignore[arg-type]
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                },
            )
        except Exception as e:
            logger.error(f"Error processing thread request: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    async def get_thread_history(
        self,
        user: User = Depends(UserRepository.get_user_by_id),  # noqa: B008
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
    ) -> EventSourceResponse:
        try:
            agent_instance = await self._get_agent_instance(thread.agent_id)
            return EventSourceResponse(
                agent_instance.load_history(thread, user),  # type: ignore[arg-type]
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                },
            )
        except Exception as e:
            logger.error(f"Error fetching thread history: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    async def feedback(
        self,
        request: FeedbackRequest,
        user: User = Depends(UserRepository.get_user_by_id),  # noqa: B008
        thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
    ) -> dict[str, str]:
        return await self._agent_service.add_feedback(
            trace=request.trace_id, feedback=request.feedback, thread=thread, user=user
        )
