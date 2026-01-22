# Flow from POV from ketenpartij (An NVI-Referral-Manager instance)

# MAIN Steps:
####### Step 1: Request OPRF token at PRS #######
# PRS uses OAuth, so we need to get an access token first
# a. Get OAuth access token using client credentials
# b. Request OPRF token for specific BSN using access token

####### Step 2: Register Referral at NVI #######
# NVI also uses OAuth, so we need to get an access token first
# a. Get OAuth access token using client credentials
# b. Register Referral using access token and OPRF token

####### Step 3: Query status of Referral at NVI #######
# a. Get OAuth access token using client credentials
# b. Query status of Referral using access token

from typing import Any
from test_flow.JWT import JWTBuilder
from test_flow.NVI import NVI
from test_flow.PRS import PRS
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.data import (
    KETENPARTIJ_ORGANIZATION_TYPE,
    KETENPARTIJ_URA_NUMBER,
    MTLS_CERT_PATH,
    MTLS_KEY_PATH,
    NVI_ENDPOINT,
    NVI_URA_NUMBER,
    OAUTH_ENDPOINT,
    PRS_ENDPOINT,
    SINGING_CERT_PATH,
    SINGING_KEY_PATH,
    TO_BE_REGISTERED_BSN,
    TO_BE_REGISTERED_CARE_CONTEXT,
    VERIFY_CA_PATH,
)

# 1-    OAth flow:
#           a- retrieve a bearer token with proper sub
# 2-    PRS Flow:
#           a- OAuth flow (Target PRS)
#           b- blind data (oprf)
#           c- exchange/eval
# 3-    NVI Reference registration:
#           a- OAuth flow
#           b- prs flow
#           c- register a reference for 1 patient
# 4-    retrieve data for an org:
#           a- OAuth (target NVI)
#           c- retrieve data for client URA number
#
# 5-    retrieve all references for a specific Patient and careContext:
#           a- OAuth (target NVI)
#           b- PRS flow
#           c- retrieve data for a client (pseudonym + client URA)
#
# 6-    delete all references for client URA:
#           a- OAuth (target NVI)
#           b- delete all refs for URA
#
# 7-    delete all references for a specific patient:
#           a- OAuth (target NVI)
#           b- PRS flow
#           c- delete all refs for a specific patient (no care context)
#
# 8-    delete all refs for a specific record:
#           a- OAuth (targeet NVI)
#           b- PRS flow
#           c- delete specific ref (with care context)
#
# 9-    Loccalise a patient:
#           a- OAuth (target NVI)
#           b- PRS flow
#           c- localise using proper Parameters (FHIR)


class DemoFlow:
    def __init__(
        self,
    ) -> None:
        self.nvi = NVI(NVI_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)
        jwt_builder = JWTBuilder(
            token_url=f"{OAUTH_ENDPOINT}/oauth/token",
            mtls_cert_path=MTLS_CERT_PATH,
            signing_cert_path=SINGING_CERT_PATH,
            signing_key_path=SINGING_KEY_PATH,
        )
        self.oauth = OAuth(OAUTH_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH, jwt_builder)
        self.prs = PRS(PRS_ENDPOINT, MTLS_CERT_PATH, MTLS_KEY_PATH, VERIFY_CA_PATH)

    def step_1_request_oprf_token(self) -> tuple[str, str]:
        """
        Step 1: Request OPRF token at PRS.
        Returns blind_factor and oprf_jwe.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="prs:read",
            target_audience=PRS_ENDPOINT,
            with_jwt=False,
        )
        blind_factor, blinded_input = OPRF.create_blinded_input(
            personal_identifier={
                "landCode": "NL",
                "type": "BSN",
                "value": TO_BE_REGISTERED_BSN,
            },
            recipient_organization="ura:" + NVI_URA_NUMBER,
            recipient_scope="nationale-verwijsindex",
        )
        oprf_jwe = self.prs.evaluate_oprf(
            blinded_input=blinded_input,
            bearer_token=bearer_token,
            recepient_org=f"ura:{NVI_URA_NUMBER}",
        )
        return blind_factor, oprf_jwe

    def step_2_register_referral(self, pseudonym: str, blind_factor: str) -> Any:
        """
        Step 2: Register Referral at NVI.
        Returns the NVI registration response.
        """
        bearer_token = self.oauth.get_bearer_token(
            scope="epd:write",
            target_audience=NVI_ENDPOINT,
            with_jwt=False,
        )
        response = self.nvi.register(
            ura_number=KETENPARTIJ_URA_NUMBER,
            bearer_token=bearer_token,
            source_type=KETENPARTIJ_ORGANIZATION_TYPE,
            pseudonym=pseudonym,
            oprf_key=blind_factor,
            care_context=TO_BE_REGISTERED_CARE_CONTEXT,
        )
        return response


if __name__ == "__main__":
    demo_flow = DemoFlow()

    blind_factor, oprf_jwe = demo_flow.step_1_request_oprf_token()

    registered_data_reference = demo_flow.step_2_register_referral(pseudonym=oprf_jwe, blind_factor=blind_factor)
