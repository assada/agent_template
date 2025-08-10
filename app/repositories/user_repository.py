import logging

from fastapi import HTTPException

from app.infrastructure.database.session import SessionManager
from app.models import User

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def get_user_by_id(self, user_id: str) -> User | None:
        try:
            if user_id is None:
                raise HTTPException(status_code=400, detail="Invalid user ID")

            # TODO: get user from database or api?
            user = User(id=user_id, email=f"user{user_id}@example.com")

            if not user:
                return None

            logger.debug(f"Resolved user: {user.id} - {user.email}")
            return user

        except ValueError as ve:
            raise HTTPException(
                status_code=400, detail="Invalid user ID format"
            ) from ve
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving user {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error") from e
