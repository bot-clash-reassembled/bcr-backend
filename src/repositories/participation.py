from collections.abc import Sequence

from sqlalchemy import select, func, bindparam, true as sa_true
from sqlalchemy.ext.asyncio import AsyncSession

from models.participation import Participation


class ParticipationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, participation_id: int) -> Participation | None:
        return await self.session.get(Participation, participation_id)

    async def list_by_user(self, user_id: int) -> Sequence[Participation]:
        result = await self.session.execute(
            select(Participation).where(Participation.user_id == user_id)
        )
        return result.scalars().all()

    async def list_all_by_league(self, league_id: int) -> Sequence[Participation]:
        result = await self.session.execute(
            select(Participation).where(Participation.league_id == league_id)
        )
        return result.scalars().all()

    async def list_top_by_league(self, league_id: int) -> Sequence[Participation]:
        result = await self.session.execute(
            select(Participation)
            .where(
                Participation.league_id == league_id,
                Participation.is_active,
            )
            .order_by(Participation.total_score.desc())
            .limit(10)
        )
        return result.scalars().all()

    async def list_top_by_participation(
        self, league_id: int, participation_id: int
    ) -> Sequence:
        ranked = (
            select(
                Participation.id,
                Participation.user_id,
                Participation.total_score,
                Participation.battles_total,
                Participation.battles_won,
                func.row_number()
                .over(
                    order_by=[
                        Participation.total_score.desc(),
                        Participation.battles_total.desc(),
                        Participation.battles_won.desc(),
                        Participation.id.asc(),
                    ]
                )
                .label("position"),
                func.count().over().label("total_count"),
            )
            .where(
                Participation.league_id == bindparam("league_id"),
                Participation.is_active,
            )
            .cte("ranked")
        )

        target = (
            select(
                ranked.c.position.label("target_position"),
                ranked.c.total_count,
            )
            .where(ranked.c.id == bindparam("participation_id"))
            .cte("target")
        )

        start_position = func.greatest(
            1,
            func.least(
                target.c.target_position - 4,
                target.c.total_count - 8,
            ),
        ).label("start_position")

        bounds = select(start_position).select_from(target).cte("bounds")

        query = (
            select(
                ranked.c.id,
                ranked.c.user_id,
                ranked.c.total_score,
                ranked.c.position,
            )
            .select_from(
                ranked.join(
                    bounds,
                    sa_true(),
                )
            )
            .where(
                ranked.c.position.between(
                    bounds.c.start_position,
                    bounds.c.start_position + 8,
                )
            )
            .order_by(
                ranked.c.position,
                ranked.c.battles_total,
                ranked.c.battles_won,
                ranked.c.id,
            )
        )

        result = await self.session.execute(
            query,
            {
                "league_id": league_id,
                "participation_id": participation_id,
            },
        )
        return result.all()

    async def create(
        self, user_id: int, design_id: int, league_id: int
    ) -> Participation:
        result = Participation(
            user_id=user_id, design_id=design_id, league_id=league_id
        )
        self.session.add(result)
        return result

    async def delete(self, participation_id: int):
        participation = await self.session.get(Participation, participation_id)
        if participation is None:
            return
        await self.session.delete(participation)
