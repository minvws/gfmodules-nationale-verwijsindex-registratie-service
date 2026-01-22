from test_flow.NVI import NVI
from test_flow.OAuth import OAuth
from test_flow.data import NVI_ENDPOINT

def delete_by_id(oauth_service: OAuth, nvi_service: NVI, reference_id: str) -> None:
    print("Deleting referral with ID:", reference_id)
    nvi_token = oauth_service.get_bearer_token(scope="epd:write", target_audience=NVI_ENDPOINT, with_jwt=True)
    resp = nvi_service.delete_by_id(
        reference_id=reference_id,
        bearer_token=nvi_token,
    )
    print("Response from delete_by_id:")
    print(resp)