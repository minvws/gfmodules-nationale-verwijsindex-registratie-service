import logging

from app.config import Config
from app.models.ura_number import UraNumber

logger = logging.getLogger(__name__)


def get_cert(path: str) -> str | None:
    try:
        with open(path, "r") as b:
            data = b.read()
        return data
    except IOError as e:
        logger.error(e)
        return None


class UraNumberService:
    @staticmethod
    def get_ura_number(config: Config) -> UraNumber:
        # attempt to get config from certificate
        logger.info("Attempting to extract UraNumber from UziCertificate")
        referral_config = config.referral_api
        if referral_config.mtls_ca:
            cert_data = get_cert(referral_config.mtls_ca)

            ura_number = UraNumber.from_certificate(cert_data)
            if ura_number:
                logger.info(
                    "Extracting UraNumber from certificate is succsseful, will use this number in the app"
                )
                return ura_number

        # no ura number found anywhere
        if not config.app.ura_number:
            raise RuntimeError(
                "Cannot start application if no UraNumber exits in uzi certificate or app config"
            )

        logger.info(
            "No UraNumber found in Certificate, will default to the one in the config"
        )
        # get the one from config
        ura_number = UraNumber(config.app.ura_number)
        return ura_number
