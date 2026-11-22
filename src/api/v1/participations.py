from fastapi import APIRouter, HTTPException, status, Response

from api.deps.auth import RequireUserDep
from api.deps.design import DesignServiceDep
from api.deps.league import LeagueServiceDep
from api.deps.participation import ParticipationServiceDep
from core.config import settings
from schemas.participation import ParticipationCreate, ParticipationRead

router = APIRouter(prefix="/participations", tags=["participations"])


@router.get("", response_model=list[ParticipationRead])
async def list_participations(
    service: ParticipationServiceDep, current_user: RequireUserDep
):
    all_participations = await service.list_user_participations(user_id=current_user.id)
    # NOTE: Add filtering by is_active if needed
    return (p for p in all_participations if p.is_active)


@router.post("", response_model=ParticipationRead)
async def create_participation(
    participation_request: ParticipationCreate,
    participation_service: ParticipationServiceDep,
    design_service: DesignServiceDep,
    league_service: LeagueServiceDep,
    current_user: RequireUserDep,
):
    league_id = (
        participation_request.league_id
        or current_user.default_league_id
        or settings.global_default_league_id
    )
    if league_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League to participate is not specified",
        )

    league_to_join = await league_service.get_league_by_id(league_id)
    if league_to_join is None or league_to_join.is_finished:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="League to participate is missing or already finished",
        )

    design_to_participate = await design_service.get_design_by_id(
        participation_request.design_id, current_user.id
    )
    if design_to_participate is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Design with ID={participation_request.design_id} not found",
        )

    return await participation_service.join_league(
        current_user.id,
        participation_request.design_id,
        league_id,
    )


@router.delete("/{participation_id}")
async def delete_participation(
    participation_id: int,
    service: ParticipationServiceDep,
    current_user: RequireUserDep,
):
    participation = await service.get_participation(participation_id)
    if participation is None or participation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participation with ID={participation_id} not found",
        )

    await service.leave_league(participation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
