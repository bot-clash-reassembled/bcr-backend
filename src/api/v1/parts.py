from fastapi import APIRouter

from api.deps.part import PartServiceDep

router = APIRouter(prefix="/parts", tags=["parts"])


@router.get("")
async def list_parts(service: PartServiceDep):
    return await service.list_parts()
