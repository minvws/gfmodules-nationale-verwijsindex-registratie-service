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
        logger.info("Attempting to extract UraNumber from UziCertificate")
        if not config.referral_api.mtls_cert:
            raise RuntimeError(
                "Unable to find mTLS Certificate path, please check app.conf for correct values especially 'referral_api' section."
            )

        cert_data = get_cert(config.referral_api.mtls_cert)
        if cert_data is None:
            raise RuntimeError("Unable to extract certificate data from file, check path or file format.")

        ura_number = UraNumber.from_certificate(cert_data)
        if not ura_number:
            raise RuntimeError(
                "Unable to start application if UraNumber does not exist in certificate, please verify that the certificate is valid."
            )

        return ura_number
