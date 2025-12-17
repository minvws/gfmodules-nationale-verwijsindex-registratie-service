from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from app.models.pseudonym import PseudonymRequest
from app.services.pseudonym import PseudonymError, PseudonymService

PATCHED_MODULE = "app.services.pseudonym.GfHttpService.do_request"


@pytest.fixture
def mock_dto() -> PseudonymRequest:
    return PseudonymRequest(
        encrypted_personal_id="some_encrypted_personal_id",
        recipient_organization="some_id",
        recipient_scope="some_scope",
    )


@patch(PATCHED_MODULE)
def test_register_should_succeed(
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
    mock_dto: PseudonymRequest,
) -> None:
    expected_jwe_token = "some_jwe_token"
    mock_response_json = {"jwe": expected_jwe_token}

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = mock_response_json
    mock_post.return_value = mock_response

    actual = pseudonym_service.submit(mock_dto)
    mock_post.assert_called_once_with(
        method="POST",
        sub_route="oprf/eval",
        data={
            "encrypted_personal_id": mock_dto.encrypted_personal_id,
            "recipient_organization": mock_dto.recipient_organization,
            "recipient_scope": mock_dto.recipient_scope,
        },
    )

    assert actual.jwe == expected_jwe_token


@patch(PATCHED_MODULE)
def test_register_should_timeout_when_there_is_no_connection(
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
    mock_dto: PseudonymRequest,
) -> None:
    mock_post.side_effect = Timeout("Request time out")

    with pytest.raises(PseudonymError):
        pseudonym_service.submit(mock_dto)

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_register_should_fail_when_server_is_down(
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
    mock_dto: PseudonymRequest,
) -> None:
    mock_post.side_effect = ConnectionError

    with pytest.raises(PseudonymError):
        pseudonym_service.submit(mock_dto)

    mock_post.assert_called_once()
