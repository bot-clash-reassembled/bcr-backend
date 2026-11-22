from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from models.notification import Notification
from repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notifications = NotificationRepository(session)

    async def list_notifications(self, receiver_id: int) -> Sequence[Notification]:
        return await self.notifications.get_by_receiver_id(receiver_id)

    async def create_notification(self, receiver_id: int, message: str) -> Notification:
        notification = await self.notifications.create(receiver_id, message)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
