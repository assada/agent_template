import logging
from datetime import UTC, datetime

from fastapi import HTTPException, Path
from sqlalchemy import desc, nullslast
from sqlmodel import select

from app.infrastructure.database.session import SessionManager
from app.models import Thread

logger = logging.getLogger(__name__)


class ThreadRepository:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def get_thread_by_id(
        self,
        thread_id: str = Path(..., description="Thread ID"),
    ) -> Thread:
        try:
            if thread_id is None or not isinstance(thread_id, str):
                raise HTTPException(status_code=400, detail="Invalid thread ID")

            with self.session_manager.get_session() as session:
                statement = select(Thread).where(Thread.id == thread_id)
                results = session.exec(statement)
                thread = results.first()

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

    async def create_thread(self, thread: Thread) -> Thread:
        try:
            with self.session_manager.get_session() as session:
                session.add(thread)
                session.commit()
                session.refresh(thread)
            logger.debug(f"Created thread: {thread.id}")
            return thread
        except Exception as e:
            logger.error(f"Error creating thread {thread.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    async def update_thread(self, thread: Thread) -> Thread:
        try:
            thread.updated_at = datetime.now(UTC)
            with self.session_manager.get_session() as session:
                session.add(thread)
                session.commit()
                session.refresh(thread)
            logger.debug(f"Updated thread: {thread.id}")
            return thread
        except Exception as e:
            logger.error(f"Error updating thread {thread.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    def list_threads_by_user(self, user_id: str) -> list[Thread]:
        try:
            with self.session_manager.get_session() as session:
                statement = (
                    select(Thread)
                    .where(Thread.user_id == user_id)
                    .order_by(
                        nullslast(desc("updated_at")),
                        desc("created_at"),
                    )
                )
                results = session.exec(statement)
                threads = list(results.all())
            logger.debug(f"Found {len(threads)} threads for user {user_id}")
            return threads
        except Exception as e:
            logger.error(f"Error listing threads for user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e

    def delete_thread(self, thread: Thread) -> None:
        try:
            with self.session_manager.get_session() as session:
                session.delete(thread)
                session.commit()
            logger.debug(f"Deleted thread: {thread.id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting thread {thread.id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e
