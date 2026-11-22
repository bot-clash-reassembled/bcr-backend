from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_receiver_id(self, receiver_id: int) -> Sequence[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.receiver_id == receiver_id)
            .order_by(Notification.date.desc())
            .limit(5)
        )
        return result.scalars().all()

    async def create(self, receiver_id: int, message: str) -> Notification:
        notification = Notification(receiver_id=receiver_id, message=message)
        self.session.add(notification)
        return notification
