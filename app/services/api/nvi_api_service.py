import logging

from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
from app.services.api.api_service import GfApiService

logger = logging.getLogger(__name__)


class NviApiService(GfApiService[Referral, CreateReferralDTO]):
    def get_referrals(self, payload: ReferralQueryDTO) -> Referral | None:
        try:
            response = self._do_request(method="POST", sub_route="registrations/query", data=payload.model_dump())
        except Exception as e:
            logger.error(f"Failed to fetch referrals: {e}")
            return None

        data = response.json()
        referrals = Referral(**data[0])
        return referrals

    def submit(self, data: CreateReferralDTO) -> Referral:
        response = self._do_request(method="POST", sub_route="registrations", data=data.model_dump())
        logging.info(f"Updating NVI with new referrals: {data}")
        new_referral = Referral(**response.json())
        return new_referral
