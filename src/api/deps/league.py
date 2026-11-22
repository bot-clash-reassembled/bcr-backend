from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from services.league import LeagueService


async def get_league_service(session: AsyncSession = Depends(get_db)):
    return LeagueService(session)


LeagueServiceDep = Annotated[LeagueService, Depends(get_league_service)]
