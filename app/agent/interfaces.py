from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Protocol

from app.bootstrap.config import AppConfig
from app.models import Thread, User


class AgentInstance(ABC):
    def __init__(self, agent_id: str, config: AppConfig):
        self.agent_id = agent_id
        self.config = config

    @abstractmethod
    async def stream_response(
        self, message: str, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        pass

    @abstractmethod
    async def load_history(
        self, thread: Thread, user: User
    ) -> AsyncGenerator[dict[str, Any]]:
        pass


class AgentFactoryProtocol(Protocol):
    async def create_agent(self, agent_id: str) -> AgentInstance: ...
