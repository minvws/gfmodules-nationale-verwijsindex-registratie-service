import logging

from app.data import Pseudonym
from app.models.pseudonym import Pseudonym as PseudonymModel
from app.models.pseudonym import PseudonymCreateDto
from app.services.api.api_service import GfApiService

logger = logging.getLogger(__name__)


class PseudonymError(Exception):
    pass


class PseudonymApiService(GfApiService[PseudonymModel, PseudonymCreateDto]):
    def __init__(
        self,
        provider_id: str,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ) -> None:
        super().__init__(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            mtls_ca=mtls_ca,
        )
        self._provider_id = provider_id

    def submit(self, data: PseudonymCreateDto) -> PseudonymModel:
        if data.provider_id is None:
            data.provider_id = self._provider_id

        logger.info(f"Exchanging BSN for provider {data.provider_id}")

        try:
            response = self._do_request(
                method="POST",
                sub_route="/register",
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
