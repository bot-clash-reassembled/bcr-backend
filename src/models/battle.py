from typing import List

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    designs: Mapped[List] = mapped_column(JSONB)
    events: Mapped[List] = mapped_column(JSONB)
    participation_ids: Mapped[List] = mapped_column(JSONB)
    winner_design_id: Mapped[int | None] = mapped_column(nullable=True)
