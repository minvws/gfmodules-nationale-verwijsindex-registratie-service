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
        default_organization_type: str,
        nvi_ura_number: UraNumber,
    ) -> None:
        self.nvi_service = nvi_service
        self.pseudonym_service = pseudonym_service
        self._ura_number = ura_number
        self._default_organization_type = default_organization_type
        self._nvi_ura_number = nvi_ura_number

    def register(self, bsn: BSN, data_domain: DataDomain) -> ReferralEntity | None:
        recipient_organization = "ura:" + self._nvi_ura_number.value
        recipient_scope = "nationale-verwijsindex"
        personal_identifier = PersonalIdentifier(land_code="NL", type="BSN", value=str(bsn))

        blind_factor, blinded_input = OprfService.create_blinded_input(
            personal_identifier, recipient_organization, recipient_scope
        )

        pseudonym = self.pseudonym_service.submit(
            PseudonymRequest(
                encrypted_personal_id=blinded_input,
                recipient_organization=recipient_organization,
                recipient_scope=recipient_scope,
            )
        )

        referral_registered = self.nvi_service.is_referral_registered(
            ReferralQuery(
                oprf_jwe=pseudonym,
                blind_factor=blind_factor,
                data_domain=data_domain,
                ura_number=self._ura_number,
            )
        )

        if referral_registered:
            logger.info(f"referral for {pseudonym.jwe} and data domain {data_domain} already registered")
            return None

        new_referral = self.nvi_service.submit(
            CreateReferralRequest(
                oprf_jwe=pseudonym,
                blind_factor=blind_factor,
                data_domain=data_domain,
                ura_number=self._ura_number,
                organization_type=self._default_organization_type,
            )
        )

        return new_referral
