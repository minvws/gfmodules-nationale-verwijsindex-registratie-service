from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from app.services.pseudonym import PseudonymError, PseudonymService

PATCHED_MODULE = "app.services.pseudonym.GfHttpService.do_request"
PATCHED_OAUTH = "app.services.oauth.oauth_service.OauthService.fetch_token"

BLINDED_INPUT = "some_encrypted_personal_id"
RECIPIENT_ORGANIZATION = "some_id"
RECIPIENT_SCOPE = "some_scope"


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_evaluate_should_succeed(
    mock_fetch_token: MagicMock,
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
) -> None:
    expected_jwe_token = "some_jwe_token"

    mock_fetch_token.return_value = MagicMock(access_token="some_access_token")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"jwe": expected_jwe_token}
    mock_post.return_value = mock_response

    actual = pseudonym_service.evaluate(
        blinded_input=BLINDED_INPUT,
        recipient_organization=RECIPIENT_ORGANIZATION,
        recipient_scope=RECIPIENT_SCOPE,
    )
    mock_post.assert_called_once_with(
        method="POST",
        sub_route="oprf/eval",
        json={
            "encryptedPersonalId": BLINDED_INPUT,
            "recipientOrganization": RECIPIENT_ORGANIZATION,
            "recipientScope": RECIPIENT_SCOPE,
        },
        headers={"Authorization": "Bearer some_access_token"},
    )

    assert actual == expected_jwe_token


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_evaluate_should_raise_when_there_is_no_connection(
    mock_fetch_token: MagicMock,
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
) -> None:
    mock_post.side_effect = Timeout("Request time out")
    mock_fetch_token.return_value = MagicMock(access_token="some_access_token")

    with pytest.raises(PseudonymError):
        pseudonym_service.evaluate(
            blinded_input=BLINDED_INPUT,
            recipient_organization=RECIPIENT_ORGANIZATION,
            recipient_scope=RECIPIENT_SCOPE,
        )

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
@patch(PATCHED_OAUTH)
def test_evaluate_should_fail_when_server_is_down(
    mock_fetch_token: MagicMock,
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
) -> None:
    mock_post.side_effect = ConnectionError
    mock_fetch_token.return_value = MagicMock(access_token="some_access_token")

    with pytest.raises(PseudonymError):
        pseudonym_service.evaluate(
            blinded_input=BLINDED_INPUT,
            recipient_organization=RECIPIENT_ORGANIZATION,
            recipient_scope=RECIPIENT_SCOPE,
        )

    mock_post.assert_called_once()
