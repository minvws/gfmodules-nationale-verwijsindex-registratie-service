from test_flow.NVIList import NVIList
from test_flow.OAuth import OAuth
from test_flow.data import NVI_ENDPOINT


def get_list_by_id(
    oauth_service: OAuth,
    nvi_list_service: NVIList,
    list_id: str,
) -> None:
    print("Retrieving FHIR List entry with ID:", list_id)
    nvi_token = oauth_service.get_bearer_token(scope="epd:read", target_audience=NVI_ENDPOINT, with_jwt=True)
    result = nvi_list_service.get_by_id(list_id=list_id, bearer_token=nvi_token)
    print("Retrieved list entry:")
    print(result)
