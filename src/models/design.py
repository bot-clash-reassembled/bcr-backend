from typing import Dict, Any

from sqlalchemy import String, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Design(Base):
    __tablename__ = "designs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(30))
    color: Mapped[str] = mapped_column(String(7))
    parts: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    slot: Mapped[int] = mapped_column()

    __table_args__ = (UniqueConstraint("user_id", "slot", name="uq__user_id_slot"),)
