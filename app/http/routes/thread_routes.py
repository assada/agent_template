from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from app.bootstrap.config import get_config
from app.http.controllers import ThreadController
from app.http.middleware import get_current_user
from app.http.requests import FeedbackRequest
from app.http.responses import ErrorResponse
from app.models import Thread, User
from app.repositories import ThreadRepository

thread_router = APIRouter(tags=["threads"])
thread_controller = ThreadController(get_config())


@thread_router.get(
    "/threads/{thread_id}",
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
async def get_thread(
    user: User = Depends(get_current_user),  # noqa: B008
    thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
) -> dict[str, str | Any]:
    return {
        "thread_id": thread.id,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "updated_at": datetime.now(tz=UTC).isoformat(),
        "metadata": {
            "title": "Thread Title",
            "user_id": user.id,
        },
        "status": "idle",
    }


@thread_router.delete(
    "/threads/{thread_id}",
    response_model=None,
    status_code=204,
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
async def delete_thread(
    request: Request,
    user: User = Depends(get_current_user),  # noqa: B008
    thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
) -> ErrorResponse | None:
    # await ThreadRepository.delete_thread(thread.id)
    return None


@thread_router.get(
    "/threads/{thread_id}/history",
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
async def get_thread_history(
    request: Request,
    user: User = Depends(get_current_user),  # noqa: B008
    thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
) -> EventSourceResponse:
    return await thread_controller.get_thread_history(user, thread)


@thread_router.post("/threads/{thread_id}/feedback")
async def post_thread_feedback(
    request: Request,
    request_body: FeedbackRequest,
    user: User = Depends(get_current_user),  # noqa: B008
    thread: Thread = Depends(ThreadRepository.get_thread_by_id),  # noqa: B008
) -> dict[str, str]:
    return await thread_controller.feedback(request_body, user, thread)
