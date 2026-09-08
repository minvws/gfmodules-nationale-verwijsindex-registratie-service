from test_flow.data import SUBJECT_IDENTIFIER_SYSTEM
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth


def query_list(
    nvi_oauth_service: OAuth,
    nvi_list_service: NVIList,
    subject: str | None = None,
    code: str | None = None,
) -> None:
    print("Querying FHIR List entries")
    nvi_token = nvi_oauth_service.get_bearer_token(scope="epd:read")
    result = nvi_list_service.query(
        bearer_token=nvi_token,
        subject_system=SUBJECT_IDENTIFIER_SYSTEM,
        subject_value=subject,
        code=code,
    )
    print("Query result:")
    print(result)
