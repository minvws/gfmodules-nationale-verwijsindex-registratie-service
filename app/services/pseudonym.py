import logging

from app.models.pseudonym import OprfPseudonymJWE
from app.models.pseudonym import PseudonymRequest
from app.services.api.http_service import GfHttpService

logger = logging.getLogger(__name__)


class PseudonymError(Exception):
    pass


class PseudonymService:
    def __init__(
        self,
        provider_id: str,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        verify_ca: str | bool,
    ) -> None:
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
        )
        self._provider_id = provider_id

    def submit(self, data: PseudonymRequest) -> OprfPseudonymJWE:
        """
        Request OPRF blinded JWE from the pseudonym service.
        """
        logger.info(
            f"Request OPRF JWE for organisation {data.recipient_organization} with scope {data.recipient_scope}"
        )

        try:
            response = self.http_service.do_request(
                method="POST", sub_route="oprf/eval", data=data.model_dump(by_alias=True)
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to request OPRF pseudonym: {e}")
            raise PseudonymError("Failed to request OPRF pseudonym") from e

        if response.status_code not in [201, 200]:
            raise PseudonymError(f"Failed to exchange BSN for pseudonym: {response.status_code}")

        try:
            response_data = response.json()
            return OprfPseudonymJWE(jwe=response_data.get("jwe"))
        except ValueError:
            raise PseudonymError("Failed to exchange BSN for pseudonym: invalid pseudonym")

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
