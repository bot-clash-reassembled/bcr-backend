from fastapi import APIRouter

from api.v1.battles import router as battles_router
from api.v1.participations import router as participations_router
from api.v1.parts import router as parts_router
from api.v1.designs import router as designs_router
from api.v1.auth import router as auth_router
from api.v1.design_templates import router as design_templates_router
from api.v1.notifications import router as notifications_router
from api.v1.leagues import router as leagues_router
from api.v1.config import router as config_router

api_router = APIRouter()
api_router.include_router(battles_router)
api_router.include_router(participations_router)
api_router.include_router(parts_router)
api_router.include_router(designs_router)
api_router.include_router(auth_router)
api_router.include_router(design_templates_router)
api_router.include_router(notifications_router)
api_router.include_router(leagues_router)
api_router.include_router(config_router)
