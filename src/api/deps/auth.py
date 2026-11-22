from typing import Annotated

from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from models.user import User
from services.auth import AuthService


def require_user(request: Request):
    user: User = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


async def get_auth_service(session: AsyncSession = Depends(get_db)):
    return AuthService(session)


RequireUserDep = Annotated[User, Depends(require_user)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
