from fastapi import APIRouter

from api.deps.design_template import DesignTemplateServiceDep


router = APIRouter(prefix="/design-templates", tags=["design-templates"])


@router.get("")
async def list_design_templates(service: DesignTemplateServiceDep):
    return await service.list_design_templates()
