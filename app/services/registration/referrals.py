import logging

from app.models.bsn import BSN
from app.models.data_domain import DataDomain
from app.models.pseudonym import PseudonymRequest, PersonalIdentifier
from app.models.referrals import CreateReferralRequest, ReferralEntity, ReferralQuery
from app.models.ura_number import UraNumber
from app.services.nvi import NviService
from app.services.oprf import OprfService
from app.services.pseudonym import PseudonymService

logger = logging.getLogger(__name__)


class ReferralRegistrationService:
    """
    Service that handles registering referrals in an NVI register by
    relying on a Pseudonym service.
    """

    def __init__(
        self,
        nvi_service: NviService,
        pseudonym_service: PseudonymService,
        ura_number: UraNumber,
    ) -> None:
        self.nvi_service = nvi_service
        self.pseudonym_service = pseudonym_service
        self._ura_number = ura_number

    def register(self, bsn: BSN, data_domain: DataDomain) -> ReferralEntity | None:
        recipient_organization = "ura:" + self._ura_number.value
        recipient_scope = "nvi"
        personal_identifier = PersonalIdentifier(land_code="NL", type="BSN", value=str(bsn))

        blind_factor, blinded_input = OprfService.create_blinded_input(personal_identifier, recipient_organization, recipient_scope)

        pseudonym = self.pseudonym_service.submit(
            PseudonymRequest(
                encrypted_personal_id=blinded_input,
                recipient_organization=recipient_organization,  # Should this not be the URA of the NVI? Or is name recipientOrganization a bit wrong?
                recipient_scope=recipient_scope,
            )
        )

        referral = self.nvi_service.get_referrals(
            ReferralQuery(
                oprf_jwe=pseudonym.jwe,
                blind_factor=blind_factor,
                data_domain=data_domain,
                ura_number=self._ura_number,
            )
        )

        if referral:
            logger.info(f"referral for {pseudonym.jwe} and data domain {data_domain} already registered")
            return None

        new_referral = self.nvi_service.submit(
            CreateReferralRequest(
                oprf_jwe=pseudonym.jwe,
                blind_factor=blind_factor,
                data_domain=data_domain,
                ura_number=self._ura_number,
                requesting_uzi_number="todo-requesting-uzi-number",  # TODO: get from config
            )
        )

        return new_referral
