import base64
import json

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models import User
from app.repositories import UserRepository

security = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
) -> User:
    try:
        token = creds.credentials
        payload = json.loads(base64.b64decode(token).decode("utf-8"))
        user_id = payload.get("user_id")
        user = await UserRepository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed") from e
