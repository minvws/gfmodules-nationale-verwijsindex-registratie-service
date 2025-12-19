import logging

from app.data import Pseudonym
from app.models.pseudonym import Pseudonym as PseudonymModel
from app.models.pseudonym import PseudonymCreateDto
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

    def submit(self, data: PseudonymCreateDto) -> PseudonymModel:
        if data.provider_id is None:
            data.provider_id = self._provider_id

        logger.info(f"Exchanging BSN for provider {data.provider_id}")

        try:
            response = self.http_service.do_request(
                method="POST",
                sub_route="register",
                data={
                    "provider_id": str(data.provider_id),
                    "bsn_hash": data.bsn.hash(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to exchange BSN for pseudonym: {e}")
            raise PseudonymError(f"Failed to exchange BSN for pseudonym: {e}")

        if response.status_code not in [201, 200]:
            raise PseudonymError(f"Failed to exchange BSN for pseudonym: {response.status_code}")

        response_data = response.json()
        try:
            new_pseudonym = Pseudonym(response_data.get("pseudonym", ""))
        except ValueError:
            raise PseudonymError("Failed to exchange BSN for pseudonym: invalid pseudonym")

        return PseudonymModel(pseudonym=str(new_pseudonym))

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
