from datetime import datetime

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    position: int
    username: str
    score: int
    country_code: str | None


class Leaderboard(BaseModel):
    league_name: str
    is_finished: bool
    next_match_date: datetime
    entries: list[LeaderboardEntry]
