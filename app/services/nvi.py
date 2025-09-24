import logging

from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
from app.services.api.http_service import GfHttpService

logger = logging.getLogger(__name__)


class NviService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ):
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            mtls_ca=mtls_ca,
        )

    def get_referrals(self, payload: ReferralQueryDTO) -> Referral | None:
        try:
            response = self.http_service.do_request(
                method="POST",
                sub_route="registrations/query",
                data=payload.model_dump(),
            )
        except Exception as e:
            logger.error(f"Failed to fetch referrals: {e}")
            return None

        data = response.json()
        referrals = Referral(**data[0])
        return referrals

    def submit(self, data: CreateReferralDTO) -> Referral:
        response = self.http_service.do_request(method="POST", sub_route="registrations", data=data.model_dump())
        logging.info(f"Updating NVI with new referrals: {data}")
        new_referral = Referral(**response.json())
        return new_referral

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
