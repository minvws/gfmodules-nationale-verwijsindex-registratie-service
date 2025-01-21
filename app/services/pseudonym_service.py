import hashlib
import logging

import requests
from requests import HTTPError

from app.data import Pseudonym, BSN

logger = logging.getLogger(__name__)


class PseudonymError(Exception):
    pass


class PseudonymService:
    _provider_id: str

    def __init__(
        self,
        endpoint: str,
        timeout: int,
        provider_id: str,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ):
        self.endpoint = endpoint
        self.timeout = timeout
        self._provider_id = provider_id
        self.mtls_cert = mtls_cert
        self.mtls_key = mtls_key
        self.mtls_ca = mtls_ca


    def exchange_for_bsn(self, bsn: BSN) -> Pseudonym:
        logger.info(f"Exchanging BSN for provider {self._provider_id}")

        bsn_hash = hashlib.sha256(str(bsn).encode()).hexdigest()

        try:
            req = requests.post(
                f"{self.endpoint}/register",
                json={
                    "provider_id": str(self._provider_id),
                    "bsn_hash": bsn_hash,
                },
                timeout=self.timeout,
                cert=(self.mtls_cert, self.mtls_key) if self.mtls_cert and self.mtls_key else None,
                verify=self.mtls_ca if self.mtls_ca else True,
            )
        except (Exception, HTTPError) as e:
            raise PseudonymError(f"Failed to exchange pseudonym: {e}")

        if req.status_code != 200:
            raise PseudonymError(f"Failed to exchange pseudonym: {req.status_code}")

        data = req.json()
        try:
            new_pseudonym = Pseudonym(data.get("pseudonym", ""))
        except ValueError:
            raise PseudonymError("Failed to exchange pseudonym: invalid pseudonym")

        return new_pseudonym


    def exchange(self, pseudonym: Pseudonym) -> Pseudonym:
        logger.info(f"Exchanging pseudonym {str(pseudonym)} for provider {self._provider_id}")

        try:
            req = requests.post(
                f"{self.endpoint}/exchange",
                json={
                    "source_pseudonym": str(pseudonym),
                    "target_provider_id": str(self._provider_id),
                },
                timeout=self.timeout,
                cert=(self.mtls_cert, self.mtls_key) if self.mtls_cert and self.mtls_key else None,
                verify=self.mtls_ca if self.mtls_ca else True,
            )
        except (Exception, HTTPError) as e:
            raise PseudonymError(f"Failed to exchange pseudonym: {e}")

        if req.status_code != 200:
            raise PseudonymError(f"Failed to exchange pseudonym: {req.status_code}")

        data = req.json()
        try:
            new_pseudonym = Pseudonym(data.get("pseudonym", ""))
        except ValueError:
            raise PseudonymError("Failed to exchange pseudonym: invalid pseudonym")

        return new_pseudonym
