from collections.abc import Sequence
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalars().first()

    async def get_system_user_by_full_name(self, full_name: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.full_name == full_name,
                User.is_system,
            )
        )
        return result.scalars().first()

    async def list_by_ids(self, user_ids: List[int]) -> Sequence[User]:
        result = await self.session.execute(select(User).where(User.id.in_(user_ids)))
        return result.scalars().all()

    async def list_system_users(self) -> Sequence[User]:
        result = await self.session.execute(select(User).where(User.is_system))
        return result.scalars().all()

    async def create(
        self,
        full_name: str,
        telegram_id: str | None = None,
        telegram_username: str | None = None,
        default_league_id: int | None = None,
        is_system: bool = False,
    ) -> User:
        result = User(
            full_name=full_name,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            default_league_id=default_league_id,
            is_system=is_system,
        )
        self.session.add(result)
        return result
