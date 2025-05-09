import logging

import requests

from app.models.referrals import CreateRefferalDTO, Referral, ReferralQueryDTO
from app.services.api.api_service import GfApiService

logger = logging.getLogger(__name__)


class NviApiService(GfApiService[Referral, CreateRefferalDTO]):
    def get_referrals(self, payload: ReferralQueryDTO) -> Referral | None:
        response = requests.post(f"{self._base_url}/registrations/query", json=payload.model_dump())
        if response.status_code >= 400:
            logger.warning(f"No results from NVI response code {response.status_code}: {response.json()}")
            return None

        data = response.json()
        referrals = Referral(**data[0])
        return referrals

    def register(self, data: CreateRefferalDTO) -> Referral:
        response = requests.post(f"{self._base_url}/registrations", json=data.model_dump())
        response.raise_for_status()

        logging.info(f"Updating NVI with new referrals: {data}")
        new_referral = Referral(**response.json())
        return new_referral
