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

    def is_referral_registered(self, payload: ReferralQuery) -> bool:
        try:
            response = self.http_service.do_request(
                method="POST",
                sub_route="registrations/query",
                data=payload.model_dump(mode="json"),
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch referrals: {e}")
            raise e
        decoded = response.json()
        entries = decoded.get("entry", [])
        if len(entries) == 0:
            return False
        return True

    def submit(self, data: CreateReferralRequest) -> ReferralEntity:
        response = self.http_service.do_request(
            method="POST", sub_route="registrations", data=data.model_dump(mode="json")
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
