import json

from typing import Annotated

from fastapi import APIRouter, Query, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from api.deps.auth import RequireUserDep
from api.deps.battle import BattleServiceDep
from api.deps.design import DesignServiceDep
from api.deps.participation import ParticipationServiceDep
from schemas.battle import BattleCreate, BattleRead

router = APIRouter(prefix="/battles", tags=["battles"])


def _wrap_sse_event_data(data):
    return {
        "event": "message",
        "data": json.dumps(data),
    }


@router.get("", response_model=list[BattleRead])
async def list_battles(
    participation_id: int,
    battle_service: BattleServiceDep,
    participation_service: ParticipationServiceDep,
    current_user: RequireUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
):
    participation = await participation_service.get_participation(participation_id)
    if participation is None or participation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participation with ID={participation_id} not found",
        )

    battle_models = await battle_service.list_battles(participation_id, page=page)
    battle_schemas = [BattleRead.model_validate(bm) for bm in battle_models]
    for bs in battle_schemas:
        for d in bs.designs:
            del d["parts"]
    return battle_schemas


@router.post("")
async def battle_endpoint(
    request: BattleCreate,
    battle_service: BattleServiceDep,
    design_service: DesignServiceDep,
    current_user: RequireUserDep,
    simulated: Annotated[bool | None, Query()] = False,
):
    if not simulated:
        raise HTTPException(422, "Persisting battles not implemented yet")

    user_design = await design_service.get_design_by_id(
        request.user_design_id, current_user.id
    )
    if user_design is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Design with ID={request.user_design_id} not found",
        )

    random_system_design = await design_service.get_random_system_user_design()
    designs_ids = [request.user_design_id, random_system_design.id]
    return EventSourceResponse(
        await battle_service.simulate_battle(designs_ids, _wrap_sse_event_data)
    )


@router.get("/{battle_id}/replay")
async def replay_battle(
    battle_id: int,
    service: BattleServiceDep,
    current_user: RequireUserDep,
):
    event_generator_or_none = await service.replay_battle(
        battle_id, current_user.id, _wrap_sse_event_data
    )
    if event_generator_or_none is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Battle not found"
        )

    return EventSourceResponse(event_generator_or_none)
