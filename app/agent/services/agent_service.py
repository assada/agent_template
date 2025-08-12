import logging
from datetime import UTC, datetime

from langfuse import Langfuse

from app.models import Thread, User

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, langfuse_client: Langfuse):
        self._langfuse_client = langfuse_client

    async def add_feedback(
            self, trace: str, feedback: float, thread: Thread, user: User
    ) -> dict[str, str]:
        try:
            self._langfuse_client.create_score(
                trace_id=trace,
                name="user_feedback",
                value=feedback,
                data_type="NUMERIC",
                # session_id=thread.id, # Bug in Langfuse SDK, session_id is broken
                comment="User feedback on the response",
                metadata={
                    "langfuse_user_id": str(user.id),
                },
            )
            thread.updated_at = datetime.now(UTC)
            return {"status": "success", "message": "Feedback recorded successfully."}
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return {"status": "error", "message": "Failed to record feedback."}
