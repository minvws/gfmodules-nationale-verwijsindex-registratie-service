from abc import ABC, abstractmethod

from app.models.permission import OtvStubPermissionRequest


class OtvService(ABC):
    @abstractmethod
    def check_authorization(self, request: OtvStubPermissionRequest) -> bool:
        pass
