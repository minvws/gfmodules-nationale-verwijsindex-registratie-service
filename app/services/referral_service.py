import http
import logging

import requests
from requests import HTTPError

from app.data import DataDomain, Pseudonym, UraNumber

logger = logging.getLogger(__name__)


MOCK_UZI_NUMBER = "90000000"


class ApiError(Exception):
    pass


class ReferralService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        mtls_ca: str | None,
    ):
        self.endpoint = endpoint
        self.timeout = timeout
        self.mtls_cert = mtls_cert
        self.mtls_key = mtls_key
        self.mtls_ca = mtls_ca

    def is_healthy(self) -> bool:
        try:
            req = requests.get(
                f"{self.endpoint}/health",
                timeout=self.timeout,
                cert=(self.mtls_cert, self.mtls_key) if self.mtls_cert and self.mtls_key else None,
                verify=self.mtls_ca if self.mtls_ca else True,
            )
            return req.status_code == 200
        except (Exception, HTTPError):
            return False

    def create_referral(self, pseudonym: Pseudonym, data_domain: DataDomain, ura_number: UraNumber) -> None:
        logger.info("Creating refererral")

        try:
            req = requests.post(
                f"{self.endpoint}/registrations/",
                json={
                    "pseudonym": str(pseudonym),
                    "data_domain": str(data_domain),
                    "ura_number": str(ura_number),
                    "requesting_uzi_number": MOCK_UZI_NUMBER,
                },
                timeout=self.timeout,
                cert=(self.mtls_cert, self.mtls_key) if self.mtls_cert and self.mtls_key else None,
                verify=self.mtls_ca if self.mtls_ca else True,
            )
        except (Exception, HTTPError) as e:
            raise ApiError(f"Failed to register referral: {e}")

        valid_status = [
            http.HTTPStatus.OK,
            http.HTTPStatus.CREATED,
        ]

        if req.status_code not in valid_status:
            raise ApiError(f"Failed to register referral: {req.status_code}")
