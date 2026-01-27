from test_flow.NVI import NVI
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.PRS import PRS
from test_flow.data import (
    KETENPARTIJ_URA_NUMBER,
    NVI_ENDPOINT,
    NVI_URA_NUMBER,
    PRS_ENDPOINT,
)

def query_referrals(oauth_service: OAuth, prs_service: PRS, nvi_service: NVI, bsn: str|None = None, care_context: str|None = None) -> None:
    print("Querying referrals for BSN:", bsn, "and care context:", care_context)
    if bsn is not None:
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

    nvi_token = oauth_service.get_bearer_token(scope="epd:read", target_audience=NVI_ENDPOINT, with_jwt=True)
    references = nvi_service.query(
        ura_number=KETENPARTIJ_URA_NUMBER,
        bearer_token=nvi_token,
        pseudonym=pseudonym_jwe if bsn is not None else None,
        oprf_key=blinded_factor if bsn is not None else None,
        care_context=care_context,
    )
    print("Queried referrals:")
    print(references)
