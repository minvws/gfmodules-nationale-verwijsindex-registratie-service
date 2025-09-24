from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.models.referrals import CreateReferralDTO, Referral, ReferralQueryDTO
from app.services.nvi import NviService

PATCHED_MODULE = "app.services.api.api_service.ApiService._do_request"


@patch(PATCHED_MODULE)
def test_get_referrals_should_succeed(
    mock_post: MagicMock,
    nvi_api_service: NviService,
    referral_query: ReferralQueryDTO,
) -> None:
    expected = Referral(**referral_query.model_dump())
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [referral_query.model_dump()]
    mock_post.return_value = mock_response

    actual = nvi_api_service.get_referrals(referral_query)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations/query",
        data=referral_query.model_dump(),
    )
    assert expected == actual


@patch(PATCHED_MODULE)
def test_register_should_succeed(
    mock_post: MagicMock,
    nvi_api_service: NviService,
    create_referral_dto: CreateReferralDTO,
) -> None:
    expected = Referral(
        **create_referral_dto.model_dump(exclude={"requesting_uzi_number"})
    )
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = expected.model_dump()
    mock_post.return_value = mock_response

    actual = nvi_api_service.submit(create_referral_dto)

    mock_post.assert_called_once_with(
        method="POST",
        sub_route="registrations",
        data=create_referral_dto.model_dump(),
    )

    assert expected == actual


@patch(PATCHED_MODULE)
def test_register_should_fail_when_record_already_exist(
    mock_post: MagicMock,
    nvi_api_service: NviService,
    create_referral_dto: CreateReferralDTO,
) -> None:
    mock_post.side_effect = HTTPError("Conflict")

    with pytest.raises(HTTPError):
        nvi_api_service.submit(create_referral_dto)

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_register_should_fail_when_connection_times_out(
    mock_post: MagicMock,
    nvi_api_service: NviService,
    create_referral_dto: CreateReferralDTO,
) -> None:
    mock_post.side_effect = Timeout("Request timed out")

    with pytest.raises(Timeout):
        nvi_api_service.submit(create_referral_dto)

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_register_should_fail_when_no_connection_is_established(
    mock_post: MagicMock,
    nvi_api_service: NviService,
    create_referral_dto: CreateReferralDTO,
) -> None:
    mock_response = MagicMock(side_effect=ConnectionError)
    mock_post.side_effect = mock_response

    with pytest.raises(ConnectionError):
        nvi_api_service.submit(create_referral_dto)

    mock_post.assert_called_once()
