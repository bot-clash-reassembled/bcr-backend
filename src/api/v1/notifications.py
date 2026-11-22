from fastapi import APIRouter

from api.deps.auth import RequireUserDep
from api.deps.notitifcation import NotificationServiceDep
from schemas.notification import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    current_user: RequireUserDep,
    service: NotificationServiceDep,
):
    return await service.list_notifications(current_user.id)
