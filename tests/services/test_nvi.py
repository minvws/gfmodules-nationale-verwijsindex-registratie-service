from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.models.referrals import ReferralQuery, ReferralEntity, CreateReferralRequest
from app.services.nvi import NviService

PATCHED_MODULE = "app.services.nvi.GfHttpService.do_request"


@patch(PATCHED_MODULE)
def test_get_referrals_should_succeed(
    mock_post: MagicMock,
    nvi_service: NviService,
    referral_query: ReferralQuery,
) -> None:
    if referral_query.ura_number is None or referral_query.oprf_jwe is None or referral_query.data_domain is None:
        pytest.fail("referral_query is missing required fields, just for type checking")

    expected_referral = ReferralEntity(
        ura_number=referral_query.ura_number,
        pseudonym=referral_query.oprf_jwe,
        data_domain=referral_query.data_domain,
        organization_type="some_type",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [expected_referral.model_dump()]
    mock_post.return_value = mock_response

    actual = nvi_service.get_referrals(referral_query)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations/query",
        data=referral_query.model_dump(),
    )
    assert actual == expected_referral


@patch(PATCHED_MODULE)
def test_get_referrals_should_return_none_if_not_found(
    mock_post: MagicMock,
    nvi_service: NviService,
    referral_query: ReferralQuery,
) -> None:
    mock_post.side_effect = HTTPError("Not Found")

    actual = nvi_service.get_referrals(referral_query)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations/query",
        data=referral_query.model_dump(),
    )
    assert actual is None


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
