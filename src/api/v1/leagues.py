from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Query

from api.deps.auth import RequireUserDep
from api.deps.league import LeagueServiceDep
from core.config import settings

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("/my_leaderboard")
async def league_leaderboard(
    current_user: RequireUserDep,
    service: LeagueServiceDep,
    show_user_position: Annotated[bool | None, Query()] = False,
):
    league_id = current_user.default_league_id or settings.global_default_league_id
    if league_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League is not specified",
        )
    leaderboard = await service.get_league_leaderboard(
        league_id, current_user.id if show_user_position else None
    )
    if leaderboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )
    return leaderboard
