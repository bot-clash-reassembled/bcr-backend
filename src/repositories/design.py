from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.design import Design


class DesignRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, design_id: int) -> Design | None:
        return await self.session.get(Design, design_id)

    async def list_by_user(self, user_id: int) -> Sequence[Design]:
        result = await self.session.execute(
            select(Design).where(Design.user_id == user_id)
        )
        return result.scalars().all()

    async def create(
        self, user_id: int, name: str, color: str, slot: int, parts: dict
    ) -> Design:
        design = Design(user_id=user_id, name=name, color=color, slot=slot, parts=parts)
        self.session.add(design)
        return design

    async def update(
        self, design: Design, name: str, color: str, parts: dict
    ) -> Design:
        design.name = name
        design.color = color
        design.parts = parts
        return design
