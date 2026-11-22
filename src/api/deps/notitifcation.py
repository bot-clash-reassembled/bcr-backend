from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from services.notification import NotificationService


async def get_notification_service(session: AsyncSession = Depends(get_db)):
    return NotificationService(session)


NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]
