from sqlalchemy import UniqueConstraint, ForeignKey, Boolean, sql as sa_sql, Index
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Participation(Base):
    __tablename__ = "participations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id"), index=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    battles_total: Mapped[int] = mapped_column(server_default="0")
    battles_won: Mapped[int] = mapped_column(server_default="0")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa_sql.true()
    )
    total_score: Mapped[int] = mapped_column(server_default="0")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "design_id", "league_id", name="uq__user_id_design_id_league_id"
        ),
        Index(
            "ix_participations_total_score",
            total_score.desc(),
            battles_total.desc(),
            battles_won.desc(),
            id,
        ),
    )
