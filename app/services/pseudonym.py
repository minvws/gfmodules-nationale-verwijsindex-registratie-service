import logging

from app.data import Pseudonym
from app.models.bsn import BSN
from app.models.pseudonym import Pseudonym as PseudonymModel
from app.models.pseudonym import PseudonymCreateDto, ReversiblePseudonymRequest
from app.models.ura_number import UraNumber
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
        mtls_ca: str | None,
    ) -> None:
        self.http_service = GfHttpService(
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

    def request_reversible(self, dto: ReversiblePseudonymRequest) -> PseudonymModel:
        """
        Request reversible pseudonym from Pseudonym Service.
        """
        try:
            data = self.http_service.do_request(
                method="POST",
                sub_route="exchange/pseudonym",
                data=dto.model_dump(by_alias=True),
            )
            return PseudonymModel(pseudonym=data.content.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to get reversible pseudonym from Pseudonym Service: {e}")
            raise PseudonymError("Failed to get reversible pseudonym from Pseudonym Service") from e

    def make_reversible_request_dto(
        self,
        bsn: BSN,
        recipient_organization_ura: UraNumber,
    ) -> ReversiblePseudonymRequest:
        return ReversiblePseudonymRequest(
            personal_id=f"NL:BSN:{bsn.value}",
            recipient_organization="ura:" + recipient_organization_ura.value,
            recipient_scope="online-toestemmingsvoorziening-stub",
            pseudonym_type="reversible",
        )

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
