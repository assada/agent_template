from __future__ import annotations

import importlib
import logging
from typing import Any

from langfuse import Langfuse

from app.agent.config import AgentConfig
from app.agent.interfaces import AgentInstance
from app.agent.langgraph.checkpoint.resolver import CheckpointerResolver
from app.agent.prompt_resolver import PromptProviderResolver
from app.bootstrap.config import AppConfig

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self, agent_class_path: str, config: AgentConfig):
        self.agent_class_path = agent_class_path
        self.config = config


class AgentFactory:
    _registered_agents: dict[str, AgentRegistry] = {}

    def __init__(
            self,
            global_config: AppConfig,
            langfuse_client: Langfuse,
            checkpointer_resolver: CheckpointerResolver,
            prompt_provider_resolver: PromptProviderResolver,
    ):
        self.global_config = global_config
        self._langfuse_client = langfuse_client
        self._checkpointer_resolver = checkpointer_resolver
        self._prompt_provider_resolver = prompt_provider_resolver

    @classmethod
    def register_agent(
            cls, agent_id: str, agent_class_path: str, config: AgentConfig
    ) -> None:
        cls._registered_agents[agent_id] = AgentRegistry(agent_class_path, config)
        logger.info(
            f"Registered agent '{agent_id}' with class '{agent_class_path}' and config {config.model_dump()}"
        )

    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._registered_agents.keys())

    def _load_agent_class(self, agent_id: str) -> type[Any]:
        if agent_id not in self._registered_agents:
            raise ValueError(
                f"Agent '{agent_id}' not found. Available agents: {self.list_agents()}"
            )

        registry_entry = self._registered_agents[agent_id]
        class_path = registry_entry.agent_class_path

        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)

            logger.debug(
                f"Successfully loaded agent class '{class_name}' from '{module_path}'"
            )
            return agent_class  # type: ignore[no-any-return]

        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Failed to import agent class '{class_path}': {e}"
            ) from e

    async def create_agent(
            self,
            agent_id: str,
    ) -> AgentInstance:
        if agent_id not in self._registered_agents:
            raise ValueError(
                f"Agent '{agent_id}' not found. Available agents: {self.list_agents()}"
            )

        registry_entry = self._registered_agents[agent_id]
        agent_config = registry_entry.config

        checkpointer = await self._checkpointer_resolver.get_saver(agent_config.checkpoint_type)

        prompt_provider = self._prompt_provider_resolver.resolve(
            agent_config.prompt_source,
            agent_name=agent_id,
        )

        agent_class = self._load_agent_class(agent_id)

        agent_instance = agent_class(
            checkpointer=checkpointer,
            prompt_provider=prompt_provider,
            **agent_config.get_custom_params(),
        )
        compiled_graph = agent_instance.build_graph()

        from app.agent.langgraph.langgraph_agent_instance import LangGraphAgentInstance

        return LangGraphAgentInstance(
            agent_id=agent_id,
            graph=compiled_graph,
            tracing_client=self._langfuse_client,
            config=self.global_config,
        )
