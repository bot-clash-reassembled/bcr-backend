import logging

from fastapi import APIRouter, HTTPException, status, Response, Request

from api.deps.auth import RequireUserDep, AuthServiceDep
from api.shared import SESSION_TOKEN_COOKIE_NAME
from core.config import settings
from schemas.auth import LoginViaTelegramRequest
from schemas.user import UserRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def me(current_user: RequireUserDep):
    return current_user


@router.post("/login_via_telegram", response_model=UserRead)
async def login_via_telegram(
    login_request: LoginViaTelegramRequest,
    service: AuthServiceDep,
    request: Request,
    response: Response,
):
    user_by_tg_token, token_payload = await service.get_user_by_telegram_id_token(
        login_request.id_token
    )
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram ID token is either expired or invalid",
        )
    if user_by_tg_token is None:
        if not settings.new_registrations_allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="New user registrations are not allowed at the moment",
            )
        user_by_tg_token = await service.register_new_user_via_telegram(
            token_payload, request.headers.get("x-forwarded-for")
        )
    # TODO: Update existing user attributes
    session_token, token_lifespan = service.create_user_session_token(user_by_tg_token)
    response.set_cookie(
        key=SESSION_TOKEN_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=token_lifespan,
    )
    return user_by_tg_token


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=SESSION_TOKEN_COOKIE_NAME,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
