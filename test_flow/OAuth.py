from urllib.parse import urlencode
import requests

from test_flow.JWT import JWTBuilder
from test_flow.data import (
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    OAUTH_ENDPOINT,
    PRS_ENDPOINT,
    SINGING_CERT_PATH,
    SINGING_KEY_PATH,
    VERIFY_CA_PATH,
)


class OAuth:
    def __init__(
        self,
        endpoint: str,
        mtls_cert: str,
        mtls_key: str,
        verify_ca: str | bool,
    ) -> None:
        self.endpoint = endpoint
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._verify_ca = verify_ca

    def get_bearer_token(self, scope: str, target_audience: str) -> str:
        """
        Get OAuth access token
        """
        data = {
            "grant_type": "client_credentials",
            "scope": scope,
            "target_audience": target_audience,
        }

        print("payload:")
        print(data)
        response = requests.post(
            f"{self.endpoint}/oauth/token",
            data=urlencode(data),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("access_token")  # type: ignore


if __name__ == "__main__":
    oauth_service = OAuth(
        endpoint=OAUTH_ENDPOINT,
        mtls_cert=MTLS_CERT_PATH,
        mtls_key=MTLS_KEY_PATH,
        verify_ca=VERIFY_CA_PATH,
    )

    # retrieving Token for Pseudoniemendienst
    bearer_token = oauth_service.get_bearer_token(
        scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=True
    )

    print("here is the token:", bearer_token)

    bearer_token_with_jwt = oauth_service.get_bearer_token(
        scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=True
    )
    print("here is the token with client assertion:", bearer_token_with_jwt)
