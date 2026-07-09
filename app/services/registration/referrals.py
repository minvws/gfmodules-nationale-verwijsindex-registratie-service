from base64 import urlsafe_b64encode
import json
import logging
from typing import List

from fastapi.encoders import jsonable_encoder

from app.models.referrals import Referral
from app.services.nvi import NviService
from app.services.oprf import OprfService
from app.services.pseudonym import PseudonymService

logger = logging.getLogger(__name__)


class ReferralRegistrationService:
    def __init__(
        self,
        nvi_service: NviService,
        pseudonym_service: PseudonymService,
        nvi_oin: str,
    ) -> None:
        self.nvi_service = nvi_service
        self.pseudonym_service = pseudonym_service
        self._nvi_oin = nvi_oin

    def register(self, bsn: str) -> Referral | None:
        subject = self.calculate_subject(bsn)

        if (
            len(
                self.nvi_service.get_registered_referrals(
                    subject=subject,
                )
            )
            > 0
        ):
            logger.info("referral already registered")
            return None

        return self.nvi_service.add_referral(
            subject=subject,
        )

    def calculate_subject(self, bsn: str) -> str:
        recipient_organization = "oin:" + self._nvi_oin
        recipient_scope = "nvi"

        personal_identifier = {
            "landCode": "NL",
            "type": "BSN",
            "value": bsn,
        }

        blind_factor, blinded_input = OprfService.create_blinded_input(
            personal_identifier=personal_identifier,
            recipient_organization=recipient_organization,
            recipient_scope=recipient_scope,
        )

        evaluated_output = self.pseudonym_service.evaluate(
            blinded_input=blinded_input,
            recipient_organization=recipient_organization,
            recipient_scope=recipient_scope,
        )

        return self.encode_url_safe_token(evaluated_output=evaluated_output, blind_factor=blind_factor)

    @staticmethod
    def encode_url_safe_token(evaluated_output: str, blind_factor: str) -> str:
        token = {
            "evaluated_output": evaluated_output,
            "blind_factor": blind_factor,
        }
        data = json.dumps(jsonable_encoder(token))
        return urlsafe_b64encode(data.encode("utf-8")).decode("ascii")

    ##################### TEST SECTION #####################

    def localize(self, bsn: str) -> List[Referral]:
        subject = self.calculate_subject(bsn)
        return self.nvi_service.localize_referrals(subject=subject)

    def query(self, bsn: str) -> List[Referral]:
        subject = self.calculate_subject(bsn)
        return self.nvi_service.get_registered_referrals(
            subject=subject,
        )
