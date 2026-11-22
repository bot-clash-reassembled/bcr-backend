from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.battle import Battle


class BattleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, battle_id: int) -> Battle | None:
        return await self.session.get(Battle, battle_id)

    async def list_by_participation(
        self, participation_id: int, limit: int = 10, offset: int = 0
    ) -> Sequence[Battle]:
        result = await self.session.execute(
            select(Battle)
            .where(Battle.participation_ids.contains([participation_id]))
            .order_by(Battle.date.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(
        self, designs, events, participation_ids, winner_design_id
    ) -> Battle:
        battle = Battle(
            designs=designs,
            events=events,
            participation_ids=participation_ids,
            winner_design_id=winner_design_id,
        )
        self.session.add(battle)
        return battle
