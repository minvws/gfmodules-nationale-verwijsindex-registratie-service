import logging

from app.models.bsn import BSN
from app.models.pseudonym import PseudonymRequest, PersonalIdentifier
from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
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
        ura_number: str,
    ) -> None:
        self.nvi_service = nvi_service
        self.pseudonym_service = pseudonym_service
        self._ura_number = ura_number

    def register(self, bsn: BSN, data_domain: str) -> Referral | None:
        recipient_organization = "ura:" + self._ura_number
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
            ReferralQueryDTO(
                pseudonym=pseudonym.jwe,
                data_domain=data_domain,
                ura_number=self._ura_number,
            )
        )

        if referral:
            logger.info(f"referral for {pseudonym.jwe} and data domain {data_domain} already registered")
            return None

        # Encrypt the resource with symmetric key
        encrypted_lmr_id = self._lmr_encryption_service.encrypt(str(bsn))

        new_referral = self.nvi_service.submit(
            CreateReferralDTO(
                pseudonym=pseudonym.jwe,
                data_domain=data_domain,
                requesting_uzi_number=self._ura_number,
                ura_number=self._ura_number,
                encrypted_lmr_id=encrypted_lmr_id,
                oprf_blinded_jwe=pseudonym,
                oprf_blind=blind_factor,
            )
        )

        return new_referral
