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
        return self._server_healthy("metadata")

    def search(self, resource_type: str, params: Dict[str, Any] | None = None) -> Bundle:
        response = self.do_request(method="GET", sub_route=f"{resource_type}/_search", params=params)

        return Bundle.model_validate(response.json())
