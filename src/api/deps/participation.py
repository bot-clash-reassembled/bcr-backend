from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from services.participation import ParticipationService


async def get_participation_service(session: AsyncSession = Depends(get_db)):
    return ParticipationService(session)


ParticipationServiceDep = Annotated[
    ParticipationService, Depends(get_participation_service)
]
