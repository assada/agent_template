import logging
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.bootstrap.config import AppConfig
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PostgreSQLConnection(DatabaseConnection):
    def __init__(self, config: AppConfig):
        self.config = config
        self._pool: AsyncConnectionPool | None = None
        self._connection_kwargs = {
            "autocommit": True,  # Mandatory for checkpointing
            "row_factory": dict_row,  # Mandatory for checkpointing
        }

    def get_connection_string(self) -> str:
        if not self.config.database_url:
            raise ValueError("Database URL is not configured")

        return self.config.database_url

    def get_sync_connection(self) -> None:
        raise NotImplementedError(
            "Sync connection not supported in async implementation"
        )

    async def get_async_connection(self) -> AsyncConnection:
        pool = await self.get_pool()
        try:
            return await pool.getconn()  ## pool.connection()
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    async def get_pool(self) -> AsyncConnectionPool:
        if self._pool is None:
            try:
                self._pool = AsyncConnectionPool(
                    conninfo=self.get_connection_string(),
                    min_size=20,
                    max_size=50,
                    kwargs=self._connection_kwargs,
                )
                await self._pool.wait()
                logger.debug("PostgreSQL connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
                raise

        return self._pool

    async def close(self) -> Any:
        if self._pool:
            await self._pool.close()
            logger.debug("PostgreSQL connection pool closed")
