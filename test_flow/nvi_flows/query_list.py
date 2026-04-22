import base64
import json

from test_flow.data import NVI_ENDPOINT, NVI_URA_NUMBER, PRS_ENDPOINT
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.PRS import PRS


def query_list(
    prs_service: PRS,
    oauth_service: OAuth,
    nvi_list_service: NVIList,
    bsn: str | None = None,
    care_context: str | None = None,
) -> None:
    print("Querying FHIR List entries")
    nvi_token = oauth_service.get_bearer_token(scope="epd:read", target_audience=NVI_ENDPOINT, with_jwt=True)
    subject_system: str | None = None
    subject_value: str | None = None
    if bsn:
        prs_token = oauth_service.get_bearer_token(scope="prs:read", target_audience=PRS_ENDPOINT, with_jwt=True)
        blind_factor, blinded_input = OPRF.create_blinded_input(
            personal_identifier={
                "landCode": "NL",
                "type": "BSN",
                "value": bsn,
            },
            recipient_organization="ura:" + NVI_URA_NUMBER,
            recipient_scope="nationale-verwijsindex",
        )
        evaluated_oprf = prs_service.evaluate_oprf(
            blinded_input=blinded_input, bearer_token=prs_token, recepient_org="ura:" + NVI_URA_NUMBER
        )
        subject_system = "http://minvws.github.io/generiekefuncties-docs/NamingSystem/nvi-identifier"
        subject_value = base64.b64encode(
            json.dumps({"evaluated_output": evaluated_oprf, "blind_factor": blind_factor}).encode("utf8")
        ).decode()
    result = nvi_list_service.query(
        bearer_token=nvi_token,
        subject_system=subject_system,
        subject_value=subject_value,
        code=care_context,
    )
    print("Query result:")
    print(result)
