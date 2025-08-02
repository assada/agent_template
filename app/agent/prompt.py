from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    from langfuse import Langfuse as _LF  # type: ignore[attr-defined]
except ImportError:
    _LF = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)


class PromptSource(str, Enum):
    LANGFUSE = "langfuse"
    FILE = "file"
    DEFAULT = "unknown"


class Prompt(BaseModel):
    source: PromptSource = PromptSource.DEFAULT
    content: str
    config: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptProvider(ABC):
    @abstractmethod
    def get_prompt(self, prompt_name: str, label: str, fallback: Prompt) -> Prompt:
        pass


class LangfusePromptProvider(PromptProvider):
    def __init__(self, client: object):
        if _LF is None or not isinstance(client, _LF):
            raise TypeError("client must be a Langfuse instance")
        self._client = client

    def get_prompt(self, prompt_name: str, label: str, fallback: Prompt) -> Prompt:
        langfuse_prompt = self._client.get_prompt(
            name=prompt_name,
            label=label,
            fallback=fallback.content,  ## TODO: fallback not working as expected
        )

        return Prompt(
            source=PromptSource.LANGFUSE,
            content=langfuse_prompt.get_langchain_prompt(),
            config=langfuse_prompt.config if hasattr(langfuse_prompt, "config") else {},
            metadata={"langfuse_prompt": langfuse_prompt},
        )


class JsonFilePromptProvider(PromptProvider):
    """Prompt provider that reads prompts from JSON files in *root_dir*.

    File naming convention: ``<prompt_name>.json``
    Expected structure inside file::
        {
          "production": {
            "content": "System prompt text ...",
            "config": {"model": "gpt-4o-mini", "temperature": 0.7}
          },
          "dev": {"content": "Lightweight dev prompt text ..."}
        }
    If *label* is not found, *fallback* is returned.
    """

    def __init__(self, root_dir: str | Path = "agents/prompt") -> None:
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, prompt_name: str) -> Path:
        return self._root_dir / f"{prompt_name}.json"

    def get_prompt(self, prompt_name: str, label: str, fallback: Prompt) -> Prompt:
        path = self._path_for(prompt_name)
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File for {prompt_name} ({path}) not found.")
            return fallback.model_copy()
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Error reading prompt file '{path}': {exc}") from exc

        raw_entry = data.get(label)
        if raw_entry is None:
            logger.warning(
                f"Prompt '{prompt_name}' with label '{label}' not found in {path}. Using fallback."
            )
            return fallback.model_copy()

        content = raw_entry.get("content", raw_entry.get("prompt", fallback.content))
        config = raw_entry.get("config", fallback.config)

        logger.debug(f"Loaded prompt '{prompt_name}' with label '{label}' from {path}")

        return Prompt(
            source=PromptSource.FILE,
            content=content,
            config=config,
            metadata={"file_path": str(path), "label": label},
        )


def create_prompt_provider(
    prompt_source: str,
    langfuse_client: object | None = None,
    prompt_dir: str | Path | None = None,
) -> PromptProvider:
    if prompt_source.lower() == "langfuse":
        if (
            langfuse_client is None
            or _LF is None
            or not isinstance(langfuse_client, _LF)
        ):
            raise ValueError("Langfuse client is required for langfuse prompt type")
        return LangfusePromptProvider(langfuse_client)
    elif prompt_source.lower() == "file":
        return JsonFilePromptProvider(prompt_dir or "agents/prompt")
    else:
        raise ValueError(
            f"Unknown prompt source: {prompt_source}. Supported types: 'langfuse', 'file'"
        )
