from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.models.referrals import ReferralQuery, CreateReferralRequest
from app.services.nvi import NviService

PATCHED_MODULE = "app.services.nvi.GfHttpService.do_request"
PATCHED_OAUTH = "app.services.oauth.oauth_service.OauthService.fetch_token"


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_get_referrals_should_succeed(
    fetch_token: MagicMock,
    mock_post: MagicMock,
    nvi_service: NviService,
    referral_query: ReferralQuery,
) -> None:
    expected_registered = True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": "some referral data",
            }
        ],
    }
    mock_post.return_value = mock_response
    fetch_token.return_value = MagicMock(access_token="some_access_token")

    actual = nvi_service.is_referral_registered(referral_query)

    mock_post.assert_called_once_with(
        method="GET",
        sub_route="NVIDataReference",
        params=referral_query.model_dump(mode="json", by_alias=True),
        headers={"Authorization": "Bearer some_access_token", "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert actual == expected_registered


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_get_referrals_should_return_none_if_not_found(
    fetch_token: MagicMock,
    mock_post: MagicMock,
    nvi_service: NviService,
    referral_query: ReferralQuery,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            # No entries found
        ],
    }
    mock_post.return_value = mock_response
    fetch_token.return_value = MagicMock(access_token="some_access_token")

    actual = nvi_service.is_referral_registered(referral_query)

    mock_post.assert_called_once_with(
        method="GET",
        sub_route="NVIDataReference",
        params=referral_query.model_dump(mode="json", by_alias=True),
        headers={"Authorization": "Bearer some_access_token", "Content-Type": "application/x-www-form-urlencoded"},
    )

    assert actual is False


@patch(PATCHED_MODULE)
def test_register_should_fail_when_record_already_exist(
    mock_post: MagicMock,
    nvi_service: NviService,
    create_referral_dto: CreateReferralRequest,
) -> None:
    mock_post.side_effect = HTTPError("Conflict")

    with pytest.raises(HTTPError):
        nvi_service.submit(create_referral_dto)

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_register_should_fail_when_connection_times_out(
    mock_post: MagicMock,
    nvi_service: NviService,
    create_referral_dto: CreateReferralRequest,
) -> None:
    mock_post.side_effect = Timeout("Request timed out")

    with pytest.raises(Timeout):
        nvi_service.submit(create_referral_dto)

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_register_should_fail_when_no_connection_is_established(
    mock_post: MagicMock,
    nvi_service: NviService,
    create_referral_dto: CreateReferralRequest,
) -> None:
    mock_response = MagicMock(side_effect=ConnectionError)
    mock_post.side_effect = mock_response

    with pytest.raises(ConnectionError):
        nvi_service.submit(create_referral_dto)

    mock_post.assert_called_once()
