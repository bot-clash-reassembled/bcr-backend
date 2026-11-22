from fastapi import APIRouter

from core.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
async def main():
    return {
        "telegram_bot_id": settings.telegram_bot_id,
    }
