from fastapi import APIRouter, Depends

from app.container import get_authorization_check_service
from app.models.permission import PermissionRequestModel
from app.services.authorization_check_service import AuthorizationCheckService

router = APIRouter(
    prefix="/authorize",
    tags=["Permission Check Service"],
)


@router.post("", description="Permission check endpoint")
def check_permission(
    payload: PermissionRequestModel,
    auth_service: AuthorizationCheckService = Depends(get_authorization_check_service),
) -> bool:
    return auth_service.authorize(payload)
