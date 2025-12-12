import logging

from app.models.bsn import BSN
from app.models.pseudonym import PseudonymCreateDto
from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
from app.services.nvi import NviService
from app.services.pseudonym import PseudonymService
from app.services.aes_encryption_service import AesEncryptionService, AesEncryptionError

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
        lmr_encryption_service: AesEncryptionService,
    ) -> None:
        self.nvi_service = nvi_service
        self.pseudonym_service = pseudonym_service
        self._ura_number = ura_number
        self._lmr_encryption_service = lmr_encryption_service


    def register(self, bsn: BSN, data_domain: str) -> Referral | None:
        pseudonym = self.pseudonym_service.submit(PseudonymCreateDto(bsn=bsn))
        referral = self.nvi_service.get_referrals(
            ReferralQueryDTO(
                pseudonym=pseudonym.pseudonym,
                data_domain=data_domain,
                ura_number=self._ura_number,
            )
        )

        if referral:
            logger.info(f"referral for {pseudonym.pseudonym} and data domain {data_domain} already registered")
            return None

        new_referral = self.nvi_service.submit(
            CreateReferralDTO(
                pseudonym=pseudonym.pseudonym,
                data_domain=data_domain,
                requesting_uzi_number=self._ura_number,
                ura_number=self._ura_number,
            )
        )

        return new_referral
