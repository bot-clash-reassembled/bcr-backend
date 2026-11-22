from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from services.design import DesignService


async def get_design_service(session: AsyncSession = Depends(get_db)):
    return DesignService(session)


DesignServiceDep = Annotated[DesignService, Depends(get_design_service)]
