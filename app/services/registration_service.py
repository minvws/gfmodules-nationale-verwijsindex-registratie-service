import logging

import requests

from app.config import ConfigPseudonymApi
from app.models.ura_number import UraNumber

logger = logging.getLogger(__name__)


class PseudonymError(Exception):
    pass


class PrsRegistrationService:
    def __init__(self, conf: ConfigPseudonymApi, ura_number: UraNumber) -> None:
        self.conf = conf
        self._ura_number = ura_number

    def register_nvi_rs_at_prs(self) -> None:
        """
        Register the nvi_rs organization and certificate at the PRS.
        """
        logger.info("Registering nvi_rs at PRS")

        if self.conf.mock:
            logger.info("Mock mode enabled, skipping registration at PRS")
            return

        try:
            self.__register_organization()
            self.__register_certificate()
        except Exception as e:
            logger.error(f"Failed to register nvi_rs at PRS: {e}")
            raise PseudonymError("Failed to register nvi_rs at PRS") from e

    def __register_organization(self) -> None:
        """
        Register the nvi_rs organization at the PRS.
        """
        try:
            request = requests.post(
                url=f"{self.conf.endpoint}/orgs",
                json={
                    "ura": str(self._ura_number),
                    "name": "nationale-verwijsindex-registratie-service",
                    "max_key_usage": "rp",
                },
                timeout=self.conf.timeout,
                cert=(self.conf.mtls_cert, self.conf.mtls_key),  # type: ignore
                verify=self.conf.verify_ca,
            )
            if request.status_code == 409:
                logger.info("Organization already registered at PRS")
                return
            request.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to register organization: {e}")
            raise PseudonymError("Failed to register organization")

    def __register_certificate(self) -> None:
        """
        Register the nvi_rs certificate at the PRS.
        """
        try:
            request = requests.post(
                url=f"{self.conf.endpoint}/register/certificate",
                json={
                    "scope": ["nationale-verwijsindex-registratie-service"],
                },
                timeout=self.conf.timeout,
                cert=(self.conf.mtls_cert, self.conf.mtls_key),  # type: ignore
                verify=self.conf.verify_ca,
            )
            if request.status_code == 409:
                logger.info("Certificate already registered at PRS")
                return
            request.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to register certificate: {e}")
            raise PseudonymError("Failed to register certificate")
