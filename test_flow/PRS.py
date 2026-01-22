import requests

from test_flow.OPRF import OPRF
from test_flow.JWT import JWTBuilder
from test_flow.OAuth import OAuth
from test_flow.data import (
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    NVI_URA_NUMBER,
    OAUTH_ENDPOINT,
    PRS_ENDPOINT,
    SINGING_CERT_PATH,
    SINGING_KEY_PATH,
    VERIFY_CA_PATH,
)


class PRS:
    def __init__(self, endpoint: str, mtls_cert: str, mtls_key: str, verify_ca: str | bool) -> None:
        self.endpoint = endpoint
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._verify_ca = verify_ca

    def evaluate_oprf(self, blinded_input: str, bearer_token: str, recepient_org: str) -> str:
        """
        Request OPRF blinded JWE from the pseudonym service.
        """
        response = requests.post(
            f"{self.endpoint}/oprf/eval",
            json={
                "recipientOrganization": recepient_org,
                "recipientScope": "nationale-verwijsindex",
                "encryptedPersonalId": blinded_input,
            },
            headers={"Authorization": f"Bearer {bearer_token}"},
            cert=(self._mtls_cert, self._mtls_key),
            verify=self._verify_ca,
        )
        print(response.json())
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("jwe")  # type: ignore


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
    prs_service = PRS(
        endpoint=PRS_ENDPOINT,
        mtls_cert=MTLS_CERT_PATH,
        mtls_key=MTLS_KEY_PATH,
        verify_ca=VERIFY_CA_PATH,
    )

    token = oauth_service.get_bearer_token(scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=False)
    recepient_org = f"ura:{NVI_URA_NUMBER}"
    _, blinded_input = OPRF.create_blinded_input(
        personal_identifier={
            "landCode": "NL",
            "type": "BSN",
            "value": "123456789",
        },
        recipient_organization=recepient_org,
        recipient_scope="nationale-verwijsindex",
    )
    print("blinded input:")
    print(blinded_input)

    evaluated_oprf = prs_service.evaluate_oprf(
        blinded_input=blinded_input, bearer_token=token, recepient_org=recepient_org
    )
