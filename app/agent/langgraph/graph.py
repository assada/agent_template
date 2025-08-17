from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from app.agent.langgraph.base_state import BaseState, State
from app.agent.prompt import Prompt, PromptProvider

logger = logging.getLogger(__name__)


class ModelResponse(TypedDict):
    messages: list[AIMessage]
    message_trace_map: list[dict[str, str | None]]


class Graph(ABC):
    def __init__(
        self,
        checkpointer: BaseCheckpointSaver[Any],
        prompt_provider: PromptProvider,
        **kwargs: Any,
    ):
        self._checkpointer = checkpointer
        self._prompt_provider = prompt_provider
        self._custom_params = kwargs

    @property
    @abstractmethod
    def graph_name(self) -> str:
        """Name of the graph for prompt retrieval."""
        pass

    @abstractmethod
    def build_graph(self) -> CompiledStateGraph[State, BaseState, None]:
        """Build the StateGraph for the agent."""
        pass

    def get_model(self, prompt: Prompt) -> BaseChatModel:
        cfg = getattr(prompt, "config", {}) or {}
        cfg_model = cfg.get("model", "")
        provider, model = cfg_model.split("/", 1)

        return cast(
            BaseChatModel,
            init_chat_model(
                model,
                model_provider=provider,
                temperature=cfg.get("temperature"),
                max_tokens=cfg.get("max_tokens"),
            ),
        )

    def get_prompt_name(self) -> str:
        """Get the prompt name. Override if different from graph_name."""
        return self.graph_name

    def get_prompt_label(self) -> str:
        """Get the prompt label."""
        return str(self._custom_params.get("prompt_label", "production"))

    def get_prompt_fallback(self) -> Prompt:
        """Get the fallback prompt text."""
        return Prompt(
            content=self._custom_params.get(
                "default_prompt", "You are a helpful assistant."
            ),
            config={
                "model": self.get_default_model(),
                "temperature": self.get_default_temperature(),
                "max_tokens": self.get_max_tokens(),
            },
        )

    def get_default_model(self) -> str:
        """Get the default model name."""
        return str(self._custom_params.get("default_model", "openai/gpt-4o-mini"))

    def get_default_temperature(self) -> float:
        """Get the default temperature."""
        return float(self._custom_params.get("temperature", 1.0))

    def get_max_tokens(self) -> int:
        """Get the maximum number of tokens for the model. Override if needed."""
        return int(self._custom_params.get("max_tokens", 4096))

    def get_tools(self) -> list[Any]:
        """Get tools for the model. Override to provide specific tools."""
        return []

    def get_prompt_placeholders(self) -> dict[str, str]:
        """Get placeholder variables for prompt template. Override to add more."""
        return {"system_time": datetime.now(tz=UTC).isoformat()}

    def is_emergency_stop_needed(self, state: BaseState, response: AIMessage) -> bool:
        """Check if emergency stop is needed. Override for custom emergency stop logic."""
        return (
            hasattr(state, "is_last_step")
            and getattr(state, "is_last_step", False)
            and hasattr(response, "tool_calls")
        )

    def create_emergency_response(self, response: AIMessage) -> AIMessage:
        """Create emergency response when max steps reached but model still wants to call tools."""
        return AIMessage(
            id=response.id,
            content="Sorry, I could not find an answer to your question in the specified number of steps.",
        )

    @staticmethod
    def _with_tools(model: Any, tools: list[Any] | None = None) -> Any:
        return model.bind_tools(tools) if tools else model

    async def call_model(
        self, state: BaseState, config: RunnableConfig
    ) -> ModelResponse:
        """Base implementation of call_model. Can be overridden if needed."""
        prompt = self._prompt_provider.get_prompt(
            self.get_prompt_name(), self.get_prompt_label(), self.get_prompt_fallback()
        )

        model = self._with_tools(self.get_model(prompt), self.get_tools())

        template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt.content),
                MessagesPlaceholder("history"),
            ]
        ).partial(**self.get_prompt_placeholders())
        template.metadata = prompt.metadata

        chain = template | model

        response = cast(
            AIMessage,
            await chain.ainvoke(
                {"history": state.messages},
                config=config,
            ),
        )

        if self.is_emergency_stop_needed(state, response):
            response = self.create_emergency_response(response)

        metadata = config.get("metadata", {})

        return {
            "messages": [response],
            "message_trace_map": [
                *state.message_trace_map,
                {
                    "id": response.id,
                    "trace_id": metadata.get("trace_id"),
                },
            ],
        }
