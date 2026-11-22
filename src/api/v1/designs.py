from fastapi import APIRouter, HTTPException, status

from api.deps.auth import RequireUserDep
from api.deps.design import DesignServiceDep
from api.deps.part import PartServiceDep
from battle.shared import BattleObjectProperty as BOP
from schemas.design import DesignCreate, DesignRead

router = APIRouter(prefix="/designs", tags=["designs"])


async def _remap_parts(design_in: DesignCreate, parts_service: PartServiceDep):
    all_parts = await parts_service.list_parts()
    parts_resolver = {part[BOP.PART_ID]: part for part in all_parts}
    remapped_parts = {
        pos: parts_resolver[part_id]
        for pos, part_id in design_in.parts.items()
        if part_id in parts_resolver
    }
    if len(remapped_parts) != len(design_in.parts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some parts have invalid IDs",
        )
    design_in.parts = remapped_parts


@router.get("", response_model=list[DesignRead])
async def list_designs(service: DesignServiceDep, current_user: RequireUserDep):
    return await service.list_designs(user_id=current_user.id)


@router.post("", response_model=DesignRead)
async def create_design(
    design_in: DesignCreate,
    design_service: DesignServiceDep,
    parts_service: PartServiceDep,
    current_user: RequireUserDep,
):
    await _remap_parts(design_in, parts_service)
    return await design_service.create_design(
        user_id=current_user.id, design_in=design_in
    )


@router.put("/{design_id}", response_model=DesignRead)
async def update_design(
    design_id: int,
    design_in: DesignCreate,
    design_service: DesignServiceDep,
    parts_service: PartServiceDep,
    current_user: RequireUserDep,
):
    design = await design_service.get_design_by_id(design_id, current_user.id)
    if design is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Design not found"
        )

    await _remap_parts(design_in, parts_service)
    return await design_service.update_design(design, design_in)
