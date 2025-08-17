from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse

from app.container import Container
from app.http.controllers import ThreadController
from app.http.middleware.auth import get_current_user
from app.http.requests import Run
from app.models import User

runs_router = APIRouter(tags=["runs"])


@runs_router.post("/runs/stream")
@inject
async def run_stream(
    request: Run,
    thread_controller: Annotated[
        ThreadController, Depends(Provide[Container.thread_controller])
    ],
    user: User = Depends(get_current_user),  # noqa: B008
) -> EventSourceResponse:
    return await thread_controller.stream(
        request.agent_id, request.input, request.thread_id, request.metadata or {}, user
    )
