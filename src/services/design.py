import random

from sqlalchemy.ext.asyncio import AsyncSession

from models.design import Design
from repositories.design import DesignRepository
from repositories.user import UserRepository
from schemas.design import DesignCreate


class DesignService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.designs = DesignRepository(session)
        self.users = UserRepository(session)

    async def list_designs(self, user_id: int):
        return await self.designs.list_by_user(user_id)

    async def get_design_by_id(self, design_id: int, user_id: int):
        design = await self.designs.get_by_id(design_id)
        return None if design is None or design.user_id != user_id else design

    async def get_random_system_user_design(self) -> Design:
        designs_list = []
        for su in await self.users.list_system_users():
            designs_list.extend(await self.designs.list_by_user(su.id))
        return random.choice(designs_list)

    async def create_design(self, user_id: int, design_in: DesignCreate):
        design = await self.designs.create(
            user_id=user_id,
            name=design_in.name,
            color=design_in.color,
            slot=design_in.slot,
            parts=design_in.parts,
        )
        await self.session.commit()
        await self.session.refresh(design)
        return design

    async def update_design(self, design: Design, design_in: DesignCreate):
        updated_design = await self.designs.update(
            design=design,
            name=design_in.name,
            color=design_in.color,
            parts=design_in.parts,
        )
        await self.session.commit()
        await self.session.refresh(updated_design)
        return updated_design
