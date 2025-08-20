import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.langgraph.checkpoint.base import BaseCheckpointer
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PostgresCheckpointer(BaseCheckpointer):
    """PostgreSQL implementation of the checkpointer."""

    def __init__(self, database_connection: DatabaseConnection):
        self.database_connection = database_connection
        self._checkpointer: AsyncPostgresSaver | None = None

    async def initialize(self) -> None:
        """Initialize the PostgreSQL checkpointer."""
        if self._checkpointer is None:
            pool = await self.database_connection.get_pool()
            self._checkpointer = AsyncPostgresSaver(pool)
            await self._checkpointer.setup()  ## TODO: do not await
            logger.debug(
                "PostgreSQL checkpoint provider initialized with connection pool"
            )

    async def cleanup(self) -> None:
        """Clean up PostgreSQL resources."""
        self._checkpointer = None

    async def get_checkpointer(self) -> AsyncPostgresSaver:
        """Get the PostgreSQL checkpointer instance."""
        if self._checkpointer is None:
            raise ValueError("Checkpointer has not been initialized.")

        return self._checkpointer
