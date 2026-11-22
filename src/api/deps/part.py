from typing import Annotated

from fastapi import Depends

from services.part import PartService


async def get_part_service():
    return PartService()


PartServiceDep = Annotated[PartService, Depends(get_part_service)]
