from typing import Any, Dict

from fhir.resources.R4B.bundle import Bundle

from app.services.api.http_service import HttpService


class FhirHttpService(HttpService):
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ):
        super().__init__(endpoint, timeout, mtls_cert, mtls_key, mtls_ca)

    def server_healthy(self) -> bool:
        return self._server_healthy("actuator/health")

    def search(self, resource_type: str, params: Dict[str, Any] | None = None) -> Bundle:
        response = self.do_request("GET", sub_route=f"/fhir/{resource_type}", params=params)
        response.raise_for_status()

        return Bundle.model_validate(response.json())
