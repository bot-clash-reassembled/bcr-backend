from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from core.config import settings
from models.league import League
from repositories.league import LeagueRepository
from repositories.participation import ParticipationRepository
from repositories.user import UserRepository
from schemas.league import LeaderboardEntry, Leaderboard


class LeagueService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.leagues = LeagueRepository(session)
        self.participations = ParticipationRepository(session)
        self.users = UserRepository(session)

    async def list_leagues(self) -> Sequence[League]:
        return await self.leagues.get_all()

    async def get_league_by_id(self, league_id: int):
        return await self.leagues.get_by_id(league_id)

    async def get_league_leaderboard(self, league_id: int, user_id: int | None):
        league = await self.leagues.get_by_id(league_id)
        if league is None:
            return None

        leaderboard_entries = None
        if user_id:
            user_participations = await self.participations.list_by_user(user_id)
            user_league_participation = next(
                p
                for p in user_participations
                if p.league_id == league_id and p.is_active
            )
            if user_league_participation:
                leaderboard_entries = await self._get_user_leaderboard_entries(
                    league_id, user_league_participation.id
                )

        if not leaderboard_entries:
            leaderboard_entries = await self._get_top_leaderboard_entries(league_id)

        utc_now = datetime.now(timezone.utc)
        today_next_match_date = utc_now.replace(
            hour=settings.league_match_hour_utc, minute=0, second=0, microsecond=0
        )
        next_match_date_to_return = (
            today_next_match_date
            if today_next_match_date > utc_now
            else today_next_match_date + timedelta(days=1)
        )
        return Leaderboard(
            league_name=league.name,
            is_finished=league.is_finished,
            next_match_date=next_match_date_to_return,
            entries=leaderboard_entries,
        )

    async def _get_top_leaderboard_entries(self, league_id: int):
        top_league_participations = await self.participations.list_top_by_league(
            league_id
        )
        participation_users = await self.users.list_by_ids(
            [p.user_id for p in top_league_participations]
        )
        users_resolver = {user.id: user for user in participation_users}
        top_league_participations.sort(
            key=lambda p: (p.total_score, p.battles_total, p.battles_won, -p.id),
            reverse=True,
        )
        leaderboard_entries = []
        for i, p in enumerate(top_league_participations):
            if i > 8:
                break
            p_user = users_resolver[p.user_id]
            leaderboard_entries.append(
                LeaderboardEntry(
                    position=i + 1,
                    username=p_user.full_name,
                    score=p.total_score,
                    country_code=p_user.country_code,
                )
            )
        return leaderboard_entries

    async def _get_user_leaderboard_entries(
        self, league_id: int, participation_id: int
    ):
        user_league_participations = (
            await self.participations.list_top_by_participation(
                league_id, participation_id
            )
        )
        participation_users = await self.users.list_by_ids(
            [p[1] for p in user_league_participations]
        )
        users_resolver = {user.id: user for user in participation_users}
        leaderboard_entries = []
        for i, p in enumerate(user_league_participations):
            if i > 8:
                break
            p_user = users_resolver[p[1]]
            leaderboard_entries.append(
                LeaderboardEntry(
                    position=p[3],
                    username=p_user.full_name,
                    score=p[2],
                    country_code=p_user.country_code,
                )
            )
        return leaderboard_entries
