import logging
from abc import ABC, abstractmethod
from typing import Any, Literal

from requests import HTTPError, Response, request
from requests.exceptions import ConnectionError, Timeout

logger = logging.getLogger(__name__)


class HttpService(ABC):
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ):
        self._endpoint = endpoint
        self._timeout = timeout
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._mtls_ca = mtls_ca

    @abstractmethod
    def server_healthy(self) -> bool: ...

    def _server_healthy(self, sub_route: str) -> bool:
        try:
            response = self.do_request(method="GET", sub_route=sub_route)
            response.raise_for_status()
        except Exception as e:
            logger.error(e)
            return False
        return True

    def do_request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        sub_route: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ) -> Response:
        try:
            cert = (self._mtls_cert, self._mtls_key) if self._mtls_cert and self._mtls_key else None
            verify = self._mtls_ca if self._mtls_ca else True
            response = request(
                method=method,
                url=f"{self._endpoint}/{sub_route}",
                params=params,
                headers=headers,
                json=data,
                timeout=self._timeout,
                cert=cert,
                verify=verify,
            )
            response.raise_for_status()
            return response
        except (ConnectionError, Timeout) as e:
            logger.error(f"Request failed: {e}")
            raise e
        except HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise e


class GfHttpService(HttpService):
    def server_healthy(self) -> bool:
        return self._server_healthy("health")
