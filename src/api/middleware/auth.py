import logging

from fastapi import Request

from api.shared import SESSION_TOKEN_COOKIE_NAME
from core.db import SessionLocal
from services.auth import AuthService

logger = logging.getLogger(__name__)


async def populate_user_middleware(request: Request, call_next):
    request.state.user = None

    session_token = request.cookies.get(SESSION_TOKEN_COOKIE_NAME)
    if session_token:
        async with SessionLocal() as session:
            auth_service = AuthService(session)
            try:
                user_by_token = await auth_service.get_user_by_session_token(
                    session_token
                )
            except Exception as e:
                logger.error(f"An error occurred while getting user by token: {e}")
                await session.rollback()
            else:
                if user_by_token:
                    request.state.user = user_by_token
            finally:
                await session.close()

    return await call_next(request)
