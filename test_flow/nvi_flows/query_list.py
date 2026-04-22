from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.data import NVI_ENDPOINT


def query_list(
    oauth_service: OAuth,
    nvi_list_service: NVIList,
    subject_system: str | None = None,
    subject_value: str | None = None,
    source_system: str | None = None,
    source_value: str | None = None,
    code: str | None = None,
) -> None:
    print("Querying FHIR List entries")
    nvi_token = oauth_service.get_bearer_token(scope="epd:read", target_audience=NVI_ENDPOINT, with_jwt=True)
    result = nvi_list_service.query(
        bearer_token=nvi_token,
        subject_system=subject_system,
        subject_value=subject_value,
        source_system=source_system,
        source_value=source_value,
        code=code,
    )
    print("Query result:")
    print(result)
