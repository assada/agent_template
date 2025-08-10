import base64
import json
import logging
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.container import Container
from app.models import User
from app.services.user_service import UserService

security = HTTPBearer()

logger = logging.getLogger(__name__)


@inject
async def get_current_user(
    user_service: Annotated[UserService, Depends(Provide[Container.user_service])],  # noqa: B008
    creds: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
) -> User:
    try:
        token = creds.credentials
        payload = json.loads(base64.b64decode(token).decode("utf-8"))
        user_id = payload.get("user_id")
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="Authentication failed") from e
