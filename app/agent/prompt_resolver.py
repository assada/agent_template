from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from langfuse import Langfuse

from app.bootstrap.config import AppConfig

from .prompt import JsonFilePromptProvider, LangfusePromptProvider, PromptProvider


class PromptProviderResolver:
    def __init__(
        self,
        config: AppConfig,
        langfuse_client: Langfuse | None = None,
    ) -> None:
        self._config = config
        self._langfuse_client = langfuse_client
        self._registry: dict[str, Callable[[dict[str, Any]], PromptProvider]] = {
            "file": self._build_file,
            "langfuse": self._build_langfuse,
        }

    def register(
        self, source: str, factory: Callable[[dict[str, Any]], PromptProvider]
    ) -> None:
        self._registry[source.lower()] = factory

    def resolve(self, source: str, *, agent_name: str | None = None) -> PromptProvider:
        source_normalized = source.lower()
        factory = self._registry.get(source_normalized)
        if factory is None:
            raise ValueError(f"Unknown prompt source: {source_normalized}.")
        return factory({"agent_name": agent_name})

    def _build_file(self, ctx: dict[str, Any]) -> PromptProvider:
        agent_name = ctx.get("agent_name")
        if not agent_name:
            raise ValueError("agent_name is required for 'file' prompt source")
        prompt_dir = Path(self._config.prompt_root_dir) / agent_name
        return JsonFilePromptProvider(prompt_dir)

    def _build_langfuse(self, _: dict[str, Any]) -> PromptProvider:
        if self._langfuse_client is None:
            raise ValueError("Langfuse client is required for 'langfuse' prompt source")
        return LangfusePromptProvider(self._langfuse_client)
