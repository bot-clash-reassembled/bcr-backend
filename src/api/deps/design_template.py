from typing import Annotated

from fastapi import Depends

from services.design_template import DesignTemplateService


async def get_design_template_service():
    return DesignTemplateService()


DesignTemplateServiceDep = Annotated[
    DesignTemplateService, Depends(get_design_template_service)
]
