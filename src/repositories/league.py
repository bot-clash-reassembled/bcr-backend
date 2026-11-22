from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from models.league import League


class LeagueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, league_id: int) -> League | None:
        return await self.session.get(League, league_id)

    async def get_all(self) -> Sequence[League]:
        result = await self.session.execute(select(League))
        return result.scalars().all()

    async def create(self, name: str) -> League:
        league = League(name=name)
        self.session.add(league)
        return league
