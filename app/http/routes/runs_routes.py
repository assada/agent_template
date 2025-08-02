from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.bootstrap.config import get_config
from app.http.controllers import ThreadController
from app.http.middleware import get_current_user
from app.http.requests import Run
from app.models import User

runs_router = APIRouter(tags=["runs"])
thread_controller = ThreadController(get_config())


@runs_router.post("/runs/stream")
async def run_stream(
    request: Run,
    user: User = Depends(get_current_user),  # noqa: B008
) -> EventSourceResponse:
    return await thread_controller.stream(
        request.agent_id, request.input, request.thread_id, request.metadata or {}, user
    )
