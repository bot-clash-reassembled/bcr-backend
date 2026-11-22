from sqlalchemy.ext.asyncio import AsyncSession

from models.participation import Participation
from repositories.participation import ParticipationRepository


class ParticipationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.participations = ParticipationRepository(session)

    async def get_participation(self, participation_id: int) -> Participation | None:
        return await self.participations.get_by_id(participation_id)

    async def list_user_participations(self, user_id: int):
        return await self.participations.list_by_user(user_id)

    async def list_league_participations(self, league_id: int):
        return await self.participations.list_all_by_league(league_id)

    async def join_league(
        self, user_id: int, design_id: int, league_id: int
    ) -> Participation:
        user_participations = await self.participations.list_by_user(user_id)
        existing_league_participation = next(
            (p for p in user_participations if p.league_id == league_id), None
        )
        if existing_league_participation:
            existing_league_participation.design_id = design_id
            existing_league_participation.is_active = True
            await self.session.commit()
            await self.session.refresh(existing_league_participation)
            return existing_league_participation

        result = await self.participations.create(user_id, design_id, league_id)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def leave_league(self, participation_id: int):
        league_participation = await self.participations.get_by_id(participation_id)
        if league_participation is None:
            return
        league_participation.is_active = False
        await self.session.commit()
