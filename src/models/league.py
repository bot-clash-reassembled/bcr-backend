from sqlalchemy import String, Boolean, sql as sa_sql
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    is_finished: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa_sql.false()
    )
