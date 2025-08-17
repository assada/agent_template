from typing import Any, Literal

from pydantic import BaseModel


class AgentConfig(BaseModel):
    prompt_source: Literal["file", "langfuse"] = "file"
    checkpoint_type: Literal["memory", "postgres"] = "memory"

    custom_params: dict[str, Any] = {}

    def get_custom_params(self) -> dict[str, Any]:
        return self.custom_params
