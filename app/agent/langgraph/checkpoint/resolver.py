from __future__ import annotations

from typing import Any, Literal

from .base import BaseCheckpointer

CheckpointType = Literal["memory", "postgres"]


class CheckpointerResolver:
    def __init__(
        self,
        memory_checkpointer: BaseCheckpointer,
        postgres_checkpointer: BaseCheckpointer,
    ) -> None:
        self._registry: dict[str, BaseCheckpointer] = {
            "memory": memory_checkpointer,
            "postgres": postgres_checkpointer,
        }

    def resolve(self, checkpoint_type: CheckpointType) -> BaseCheckpointer:
        checkpoint_type_normalized = checkpoint_type.lower()
        if checkpoint_type_normalized not in self._registry:
            raise ValueError(
                f"Unsupported checkpointer type: {checkpoint_type_normalized}"
            )
        return self._registry[checkpoint_type_normalized]

    async def get_saver(self, checkpoint_type: CheckpointType) -> Any:
        provider = self.resolve(checkpoint_type)
        await provider.initialize()
        return await provider.get_checkpointer()


