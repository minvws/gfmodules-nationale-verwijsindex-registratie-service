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
        jwt_builder: JWTBuilder,
    ) -> None:
        self.endpoint = endpoint
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._verify_ca = verify_ca
        self._jwt_builder = jwt_builder

    def get_bearer_token(self, scope: str, target_audience: str, with_jwt: bool) -> str:
        """
        Get OAuth access token
        """
        data = {
            "grant_type": "client_credentials",
            "scope": scope,
            "target_audience": target_audience,
        }
        if with_jwt:
            print("creating client assertion type...")
            data["client_assertion_type"] = (
                "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            )
            token = self._jwt_builder.build(
                scope=scope, target_audience=target_audience
            )
            print("creating jwt token...")
            print(token)
            data["client_assertion"] = token

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
    jwt_builder = JWTBuilder(
        token_url=f"{OAUTH_ENDPOINT}/oauth/token",
        mtls_cert_path=MTLS_CERT_PATH,
        signing_cert_path=SINGING_CERT_PATH,
        signing_key_path=SINGING_KEY_PATH,
    )
    oauth_service = OAuth(
        endpoint=OAUTH_ENDPOINT,
        mtls_cert=MTLS_CERT_PATH,
        mtls_key=MTLS_KEY_PATH,
        verify_ca=VERIFY_CA_PATH,
        jwt_builder=jwt_builder,
    )

    # retrieving Token for Pseudoniemendients
    bearer_token = oauth_service.get_bearer_token(
        scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=True
    )

    print("here is the token:", bearer_token)

    bearer_token_with_jwt = oauth_service.get_bearer_token(
        scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=True
    )
    print("here is the token with client assertion:", bearer_token_with_jwt)
