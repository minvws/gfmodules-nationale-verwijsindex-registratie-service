import logging

from app.models.permission import OtvStubDto, OtvStubPermissionRequest, OtvStubResourceDto, OtvStubSubjectDto
from app.models.ura_number import UraNumber
from app.services.api.http_service import GfHttpService
from app.services.OtvService.interface import OtvService

logger = logging.getLogger(__name__)


class PermissionError(Exception):
    pass


class OtvStubService(OtvService):
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str,
        mtls_key: str | None,
        mtls_ca: str | None,
    ) -> None:
        try:
            with open(mtls_cert, "r") as cert_data:
                ura_number = UraNumber.from_certificate(cert_data.read())
                if ura_number is None:
                    raise PermissionError("Failed to read UraNumber from mtls_cert")
                self._ura_number = ura_number
        except Exception:
            logger.error("Could not set UraNumber from mtls_cert")
            raise PermissionError("Could not set UraNumber from mtls_cert")
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            mtls_ca=mtls_ca,
        )

    def check_authorization(
        self,
        request: OtvStubPermissionRequest,
    ) -> bool:
        dto = OtvStubDto(
            resource=OtvStubResourceDto(
                pseudonym=request.reversible_pseudonym.pseudonym,
                org_ura=str(self._ura_number),
                org_category="V6",  # Hardcoded for now
            ),
            subject=OtvStubSubjectDto(
                org_ura=str(request.client_ura_number),
            ),
        )

        try:
            response = self.http_service.do_request(
                method="POST",
                sub_route="permission",
                data=dto.model_dump(),
            )
        except Exception as e:
            logger.error(f"Failed to check for authorization: {e}")
            raise PermissionError("Failed to check for authorization") from e

        try:
            response_message = response.json()
            if not isinstance(response_message, bool):
                raise ValueError("Response is not a boolean")
            return response_message
        except ValueError as e:
            logger.error(f"Failed to parse response: {e}")
            raise PermissionError("Failed to parse response") from e

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
