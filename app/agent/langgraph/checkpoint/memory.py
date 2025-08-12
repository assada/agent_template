import logging

from langgraph.checkpoint.memory import InMemorySaver

from app.agent.langgraph.checkpoint.base import BaseCheckpointer

logger = logging.getLogger(__name__)


class MemoryCheckpointer(BaseCheckpointer):
    """Memory implementation of the checkpointer."""

    def __init__(self) -> None:
        self._checkpointer: InMemorySaver | None = None

    async def initialize(self) -> None:
        """Initialize the memory checkpointer."""
        if self._checkpointer is None:
            self._checkpointer = InMemorySaver()
            logger.debug("Memory checkpoint provider initialized")

    async def cleanup(self) -> None:
        """Clean up memory resources."""
        pass

    async def get_checkpointer(self) -> InMemorySaver:
        """Get the memory checkpointer instance."""
        if self._checkpointer is None:
            raise ValueError("Checkpointer has not been initialized.")

        return self._checkpointer
