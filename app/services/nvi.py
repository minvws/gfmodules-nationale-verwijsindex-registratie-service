import logging

from app.models.data_domain import DataDomain
from app.models.referrals import ReferralQuery, ReferralEntity, CreateReferralRequest
from app.models.ura_number import UraNumber
from app.services.api.http_service import GfHttpService

logger = logging.getLogger(__name__)


class NviService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        verify_ca: str | bool,
    ):
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
        )

    def get_referrals(self, payload: ReferralQuery) -> ReferralEntity | None:
        try:
            response = self.http_service.do_request(
                method="GET",
                sub_route="NVIDataReference",
                params=payload.model_dump(mode="json", by_alias=True),
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch referrals: {e}")
            return None
        decoded = response.json()
        if not decoded or not isinstance(decoded, list) or len(decoded) == 0:
            return None
        data = decoded[0]
        referrals = ReferralEntity(
            ura_number=UraNumber(data.get("ura_number")),
            pseudonym=data.get("pseudonym"),
            data_domain=DataDomain(data.get("data_domain")),
            organization_type=data.get("organization_type"),
        )
        return referrals

    def submit(self, data: CreateReferralRequest) -> ReferralEntity:
        response = self.http_service.do_request(
            method="POST", sub_route="NVIDataReference", data=data.model_dump(mode="json", by_alias=True)
        )
        response.raise_for_status()
        logging.info(f"Updating NVI with new referrals: {data}")
        resp = response.json()
        new_referral = ReferralEntity(
            ura_number=UraNumber(resp.get("ura_number")),
            pseudonym=resp.get("pseudonym"),
            data_domain=DataDomain(resp.get("data_domain")),
            organization_type=resp.get("organization_type"),
        )
        return new_referral

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
