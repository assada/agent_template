from typing import Any, Literal

from pydantic import BaseModel


class AgentConfig(BaseModel):
    prompt_source: Literal["file", "langfuse"] = "file"
    prompt_dir: str = "agents/prompt"  # For file-based prompts

    custom_params: dict[str, Any] = {}

    def get_custom_params(self) -> dict[str, Any]:
        return self.custom_params
