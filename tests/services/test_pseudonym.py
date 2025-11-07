from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from app.models.bsn import BSN
from app.models.pseudonym import PseudonymCreateDto
from app.services.pseudonym import PseudonymError, PseudonymService

PATCHED_MODULE = "app.services.pseudonym.GfHttpService.do_request"


@pytest.fixture
def mock_dto() -> PseudonymCreateDto:
    return PseudonymCreateDto(bsn=BSN("200060429"), provider_id="some_id")


@patch(PATCHED_MODULE)
def test_register_should_succeed(
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
    mock_dto: PseudonymCreateDto,
) -> None:
    expected = {"pseudonym": "83cce2aa-dcd6-4aac-b688-11e76902606b"}
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"pseudonym": "83cce2aa-dcd6-4aac-b688-11e76902606b"}
    mock_post.return_value = mock_response

    actual = pseudonym_service.submit(mock_dto)
    mock_post.assert_called_once_with(
        method="POST",
        sub_route="/register",
        data={"provider_id": mock_dto.provider_id, "bsn_hash": mock_dto.bsn.hash()},
    )

    assert actual.model_dump() == expected


@patch(PATCHED_MODULE)
def test_register_should_timeout_when_there_is_no_connection(
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
    mock_dto: PseudonymCreateDto,
) -> None:
    mock_post.side_effect = Timeout("Request time out")

    with pytest.raises(PseudonymError):
        pseudonym_service.submit(mock_dto)

    mock_post.assert_called_once()


@patch(PATCHED_MODULE)
def test_register_should_fail_when_server_is_down(
    mock_post: MagicMock,
    pseudonym_service: PseudonymService,
    mock_dto: PseudonymCreateDto,
) -> None:
    mock_post.side_effect = ConnectionError

    with pytest.raises(PseudonymError):
        pseudonym_service.submit(mock_dto)

    mock_post.assert_called_once()
