from typing import Any, Dict
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from requests.exceptions import ConnectionError, HTTPError, Timeout

from app.services.nvi import NviService

PATCHED_MODULE = "app.services.nvi.GfHttpService.do_request"
PATCHED_OAUTH = "app.services.oauth.oauth_service.OauthService.fetch_token"

LIST_ID = "123e4567-e89b-12d3-a456-426614174000"


def _list_resource() -> Dict[str, Any]:
    return {
        "resourceType": "List",
        "id": LIST_ID,
        "extension": [{"valueReference": {"identifier": {"system": "sys", "value": "12345678"}}, "url": "u"}],
        "source": {"identifier": {"system": "src", "value": "some_source"}},
    }


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_get_registered_referrals_should_return_referrals(
    fetch_token: MagicMock,
    mock_request: MagicMock,
    nvi_service: NviService,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [{"resource": _list_resource()}],
    }
    mock_request.return_value = mock_response
    fetch_token.return_value = MagicMock(access_token="some_access_token")

    actual = nvi_service.get_registered_referrals(subject="some_subject")

    assert len(actual) == 1
    assert actual[0].id == UUID(LIST_ID)
    assert actual[0].ura_number == "12345678"
    mock_request.assert_called_once()


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_get_registered_referrals_should_return_empty_when_no_entries(
    fetch_token: MagicMock,
    mock_request: MagicMock,
    nvi_service: NviService,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"resourceType": "Bundle", "type": "searchset", "entry": []}
    mock_request.return_value = mock_response
    fetch_token.return_value = MagicMock(access_token="some_access_token")

    actual = nvi_service.get_registered_referrals(subject="some_subject")

    assert actual == []


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_add_referral_should_return_referral(
    fetch_token: MagicMock,
    mock_request: MagicMock,
    nvi_service: NviService,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = _list_resource()
    mock_request.return_value = mock_response
    fetch_token.return_value = MagicMock(access_token="some_access_token")

    actual = nvi_service.add_referral(subject="some_subject")

    assert actual.id == UUID(LIST_ID)
    assert actual.ura_number == "12345678"
    mock_request.assert_called_once()


@pytest.mark.parametrize("error", [HTTPError("Conflict"), Timeout("timed out"), ConnectionError()])
@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_add_referral_should_propagate_errors(
    fetch_token: MagicMock,
    mock_request: MagicMock,
    nvi_service: NviService,
    error: Exception,
) -> None:
    fetch_token.return_value = MagicMock(access_token="some_access_token")
    mock_request.side_effect = error

    with pytest.raises(type(error)):
        nvi_service.add_referral(subject="some_subject")

    mock_request.assert_called_once()
