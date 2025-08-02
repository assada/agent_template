import logging
from datetime import UTC, datetime

from fastapi import HTTPException, Path

from app.models import Thread
from app.models.thread import ThreadStatus

logger = logging.getLogger(__name__)


class ThreadRepository:
    @staticmethod
    async def get_thread_by_id(
        thread_id: str = Path(..., description="Thread ID"),
    ) -> Thread:
        try:
            if thread_id is None or not isinstance(thread_id, str):
                raise HTTPException(status_code=400, detail="Invalid thread ID")

            # TODO: get thread from database
            thread = Thread(
                id=thread_id,
                user_id="1437ade37359488e95c0727a1cdf1786d24edce3",
                status=ThreadStatus.idle,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                agent_id="demo_agent",
                metadata={
                    "title": "Sample Thread",
                },
            )

            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            logger.debug(f"Resolved thread: {thread.id}")
            return thread

        except ValueError as ve:
            raise HTTPException(
                status_code=400, detail="Invalid thread ID format"
            ) from ve
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving thread {thread_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @staticmethod
    async def create_thread(thread: Thread) -> Thread:
        try:
            # TODO: save thread to database
            logger.debug(f"Created thread: {thread.id}")
            return thread
        except Exception as e:
            logger.error(f"Error creating thread {thread.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    @staticmethod
    async def update_thread(thread: Thread) -> Thread:
        try:
            # TODO: update thread in database
            thread.updated_at = datetime.now(UTC)
            logger.debug(f"Updated thread: {thread.id}")
            return thread
        except Exception as e:
            logger.error(f"Error updating thread {thread.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e
