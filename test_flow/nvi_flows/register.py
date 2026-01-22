from test_flow.NVI import NVI
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.PRS import PRS
from test_flow.data import (
    KETENPARTIJ_ORGANIZATION_TYPE,
    KETENPARTIJ_URA_NUMBER,
    NVI_ENDPOINT,
    NVI_URA_NUMBER,
    PRS_ENDPOINT,
)

def register(oauth_service: OAuth, prs_service: PRS, nvi_service: NVI, bsn: str, care_context: str) -> None:
    print("Registering new referral for BSN:", bsn, "and care context:", care_context)
    personal_identifier = {
        "landCode": "NL",
        "type": "BSN",
        "value": bsn,
    }
    recepient_org = f"ura:{NVI_URA_NUMBER}"
    recipient_scope = "nationale-verwijsindex"

    blinded_factor, blinded_input = OPRF.create_blinded_input(
        personal_identifier=personal_identifier,
        recipient_organization=recepient_org,
        recipient_scope=recipient_scope,
    )
    prs_token = oauth_service.get_bearer_token(scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=True)
    pseudonym_jwe = prs_service.evaluate_oprf(
        blinded_input=blinded_input, bearer_token=prs_token, recepient_org=recepient_org
    )

    nvi_token = oauth_service.get_bearer_token(scope="epd:write", target_audience=NVI_ENDPOINT, with_jwt=True)
    new_data_reference = nvi_service.register(
        ura_number=KETENPARTIJ_URA_NUMBER,
        bearer_token=nvi_token,
        source_type=KETENPARTIJ_ORGANIZATION_TYPE,
        pseudonym=pseudonym_jwe,
        oprf_key=blinded_factor,
        care_context=care_context,
    )
    print("New data reference:")
    print(new_data_reference)
