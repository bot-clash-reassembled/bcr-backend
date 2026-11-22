from sqlalchemy import Column, DateTime, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message: Mapped[str] = mapped_column(String(255))
