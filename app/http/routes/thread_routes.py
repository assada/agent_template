from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from langgraph_sdk.auth.exceptions import HTTPException
from sse_starlette import EventSourceResponse

from app.container import Container
from app.http.controllers import ThreadController
from app.http.middleware.auth import get_current_user
from app.http.requests import FeedbackRequest
from app.http.responses import ErrorResponse
from app.models import User
from app.services.thread_service import ThreadService

thread_router = APIRouter(tags=["threads"])


@thread_router.get(
    "/threads",
    responses={"422": {"model": ErrorResponse}},
)
@inject
def list_threads(  ## TODO: POST method to search threads
        thread_service: Annotated[
            ThreadService, Depends(Provide[Container.thread_service])
        ],
        user: User = Depends(get_current_user),  # noqa: B008
) -> list[dict[str, str | Any]]:
    threads = thread_service.list_threads(user.id)
    return [t.model_dump() for t in threads]


@thread_router.get(
    "/threads/{thread_id}",
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
@inject
def get_thread(
        thread_id: str,
        thread_service: Annotated[
            ThreadService, Depends(Provide[Container.thread_service])
        ],
        user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, str | Any]:
    thread = thread_service.get_thread(thread_id)
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Forbidden: You do not have access to this thread."
        )
    return thread.model_dump()


@thread_router.delete(
    "/threads/{thread_id}",
    response_model=None,
    status_code=204,
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
@inject
def delete_thread(
        thread_id: str,
        thread_service: Annotated[
            ThreadService, Depends(Provide[Container.thread_service])
        ],
        user: User = Depends(get_current_user),  # noqa: B008
) -> ErrorResponse | None:
    thread = thread_service.get_thread(thread_id)
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Forbidden: You do not have access to this thread."
        )
    thread_service.delete_thread(thread)
    return None


@thread_router.get(
    "/threads/{thread_id}/history",
    responses={"404": {"model": ErrorResponse}, "422": {"model": ErrorResponse}},
)
@inject
async def get_thread_history(
        thread_id: str,
        thread_service: Annotated[
            ThreadService, Depends(Provide[Container.thread_service])
        ],
        thread_controller: Annotated[
            ThreadController, Depends(Provide[Container.thread_controller])
        ],
        user: User = Depends(get_current_user),  # noqa: B008
) -> EventSourceResponse:
    thread = thread_service.get_thread(thread_id)
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Forbidden: You do not have access to this thread."
        )
    return await thread_controller.get_thread_history(thread, user)


@thread_router.post("/threads/{thread_id}/feedback")
@inject
async def post_thread_feedback(
        thread_id: str,
        thread_service: Annotated[
            ThreadService, Depends(Provide[Container.thread_service])
        ],
        thread_controller: Annotated[
            ThreadController, Depends(Provide[Container.thread_controller])
        ],
        request_body: FeedbackRequest,
        user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, str]:
    thread = thread_service.get_thread(thread_id)
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="Forbidden: You do not have access to this thread."
        )
    return await thread_controller.feedback(thread, request_body, user)
