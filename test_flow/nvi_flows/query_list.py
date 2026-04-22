import base64
import json

from test_flow.data import NVI_ENDPOINT, NVI_URA_NUMBER, PRS_ENDPOINT, SUBJECT_IDENTIFIER_SYSTEM
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.OPRF import OPRF
from test_flow.PRS import PRS


def query_list(
    oauth_service: OAuth,
    nvi_list_service: NVIList,
    subject: str | None = None,
    care_context: str | None = None,
) -> None:
    print("Querying FHIR List entries")
    nvi_token = oauth_service.get_bearer_token(scope="epd:read", target_audience=NVI_ENDPOINT, with_jwt=True)
    result = nvi_list_service.query(
        bearer_token=nvi_token,
        subject_system=SUBJECT_IDENTIFIER_SYSTEM,
        subject_value=subject,
        code=care_context,
    )
    print("Query result:")
    print(result)
