from app.models.permission import OtvStubPermissionRequest
from app.services.OtvService.interface import OtvService


class OtvMockService(OtvService):
    def check_authorization(self, request: OtvStubPermissionRequest) -> bool:
        # Mock implementation of the authorization check
        return True
