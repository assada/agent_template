import tracemalloc
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from langfuse import Langfuse

from app.agent.services.agent_service import AgentService
from app.models import Thread, User
from app.models.thread import ThreadStatus

tracemalloc.start()


@pytest.fixture
def mock_langfuse():
    lf = Mock(spec=Langfuse)
    span = Mock(trace_id="test_trace_id")
    span.__enter__ = Mock(return_value=span)
    span.__exit__ = Mock(return_value=None)
    lf.start_as_current_span.return_value = span
    lf.create_score = Mock()
    return lf


@pytest.fixture
def agent_service(mock_langfuse):
    return AgentService(mock_langfuse)


@pytest.fixture
def mock_thread():
    return Thread(
        id="test_thread_id",
        user_id="test_user_id",
        agent_id="test_agent_id",
        metadata={"key": "value"},
        status=ThreadStatus.idle,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_user():
    return User(id="test_user_id", email="test@example.com")


class TestAgentService:
    @pytest.mark.asyncio
    async def test_add_feedback_success(self, agent_service, mock_thread, mock_user):
        t0 = mock_thread.updated_at
        r = await agent_service.add_feedback("tr", 1.0, mock_thread, mock_user)
        assert r["status"] == "success"
        assert mock_thread.updated_at > t0
        agent_service.langfuse.create_score.assert_called_once()
