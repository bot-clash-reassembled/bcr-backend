from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from services.battle import BattleService


async def get_battle_service(session: AsyncSession = Depends(get_db)):
    return BattleService(session)


BattleServiceDep = Annotated[BattleService, Depends(get_battle_service)]
