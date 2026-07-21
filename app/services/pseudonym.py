import logging

from app.services.api.http_service import GfHttpService
from app.services.oauth.oauth_service import OauthService

logger = logging.getLogger(__name__)


class PseudonymError(Exception):
    pass


class PseudonymService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None,
        mtls_key: str | None,
        verify_ca: str | bool,
        oauth_service: OauthService,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self.http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
            extra_headers=extra_headers,
        )
        self._oauth_service = oauth_service

    def evaluate(self, blinded_input: str, recipient_organization: str, recipient_scope: str) -> str:
        logger.info("Request OPRF JWE for organisation")

        token = self._oauth_service.fetch_token(scope="prs:read")

        contents = {
            "encryptedPersonalId": blinded_input,
            "recipientOrganization": recipient_organization,
            "recipientScope": recipient_scope,
        }
        try:
            response = self.http_service.do_request(
                method="POST",
                sub_route="oprf/eval",
                json=contents,
                headers={"Authorization": f"Bearer {token.access_token}"},
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to request OPRF pseudonym: {e}")
            raise PseudonymError("Failed to request OPRF pseudonym") from e

        if response.status_code not in [201, 200]:
            raise PseudonymError(f"Failed to exchange BSN for pseudonym: {response.status_code}")

        try:
            response_data = response.json()
            return response_data.get("jwe")  # type: ignore
        except ValueError:
            raise PseudonymError("Failed to exchange BSN for pseudonym: invalid pseudonym")

    def server_healthy(self) -> bool:
        return self.http_service.server_healthy()
