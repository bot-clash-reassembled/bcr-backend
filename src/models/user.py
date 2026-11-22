from sqlalchemy import String, Boolean, UniqueConstraint, sql as sa_sql
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(128))
    telegram_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    default_league_id: Mapped[int | None] = mapped_column(nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa_sql.false()
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa_sql.false()
    )
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    __table_args__ = (UniqueConstraint("telegram_id", name="uq__telegram_id"),)
