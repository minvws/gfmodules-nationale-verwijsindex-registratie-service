import time
from typing import Any, Dict
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest

from app.services.api.http_service import HttpService
from app.services.api.oauth import OauthService
from app.services.api.oauth import Token

PATCHED_MODULE = "app.services.api.http_service.request"


@pytest.fixture
def mock_token_request_data() -> str:
    return urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "some_scope",
        }
    )


@pytest.fixture
def mock_token_response_body() -> Dict[str, Any]:
    return {
        "access_token": "some_value",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": ["some_scope"],
    }


@pytest.fixture
def mock_oauth(
    http_service: HttpService,
) -> OauthService:
    return OauthService(
        endpoint="http://example.org/oauth/token",
        timeout=1,
    )


@patch(PATCHED_MODULE)
def test_do_request_should_succeed(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_oauth: OauthService,
    mock_token_request_data: str,
) -> None:
    assert len(mock_oauth._tokens) == 0

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope="some_scope")

    assert request.call_count == 1
    assert request.call_args[1]["method"] == "POST"
    assert request.call_args[1]["url"] == "http://example.org/oauth/token"
    assert request.call_args[1]["data"] == mock_token_request_data
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.expires_in == mock_token_response_body["expires_in"]
    assert actual.scope == mock_token_response_body["scope"]

    assert len(mock_oauth._tokens) == 1
    assert mock_oauth._tokens[0].access_token == mock_token_response_body["access_token"]


@patch(PATCHED_MODULE)
def test_do_request_should_reuse_token(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.append(
        Token(
            access_token=mock_token_response_body["access_token"],
            token_type=mock_token_response_body["token_type"],
            expires_in=mock_token_response_body["expires_in"],
            scope=mock_token_response_body["scope"],
            added_at=int(time.time()),
        )
    )
    assert len(mock_oauth._tokens) == 1

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"][0])
    assert request.call_count == 0
    assert len(mock_oauth._tokens) == 1
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.expires_in == mock_token_response_body["expires_in"]
    assert actual.scope == mock_token_response_body["scope"]


@patch(PATCHED_MODULE)
def test_do_request_should_request_new_token_if_expired(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.extend(
        [
            Token(
                access_token="expired_token",
                token_type=mock_token_response_body["token_type"],
                expires_in=1,
                scope=mock_token_response_body["scope"],
                added_at=int(time.time()) - 4000,
            ),
            Token(
                access_token="expired_token_2",
                token_type=mock_token_response_body["token_type"],
                expires_in=1,
                scope=mock_token_response_body["scope"],
                added_at=int(time.time()) - 4000,
            ),
            Token(
                access_token="token_3",
                token_type=mock_token_response_body["token_type"],
                expires_in=3600,
                scope=["Different_scope"],
                added_at=int(time.time()),
            ),
        ]
    )
    assert mock_oauth._tokens[0].is_expired is True
    assert mock_oauth._tokens[1].is_expired is True

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"][0])
    assert request.call_count == 1
    assert len(mock_oauth._tokens) == 2
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.expires_in == mock_token_response_body["expires_in"]
    assert actual.scope == mock_token_response_body["scope"]
    for token in mock_oauth._tokens:
        assert token.is_expired is False
