from test_flow.data import NVI_ENDPOINT, SOURCE_IDENTIFIER_SYSTEM, SUBJECT_IDENTIFIER_SYSTEM
from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth


def delete_list(
    oauth_service: OAuth,
    nvi_list_service: NVIList,
    list_id: str | None = None,
    subject: str | None = None,
    source: str | None = None,
    code: str | None = None,
) -> None:
    print("Deleting FHIR List entries")
    nvi_token = oauth_service.get_bearer_token(scope="epd:write", target_audience=NVI_ENDPOINT, with_jwt=True)

    if list_id:
        status = nvi_list_service.delete_by_id(list_id=list_id, bearer_token=nvi_token)
        print("Delete by ID status:")
        print(status)
        return

    status = nvi_list_service.delete(
        bearer_token=nvi_token,
        subject_system=SUBJECT_IDENTIFIER_SYSTEM,
        subject_value=subject,
        source_system=SOURCE_IDENTIFIER_SYSTEM,
        source_value=source,
        code=code,
    )
    print("Delete by query status:")
    print(status)
