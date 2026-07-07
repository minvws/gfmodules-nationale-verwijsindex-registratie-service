import time
from typing import Any, Dict
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest

from app.models.token import TOKEN_EXPIRES_IN, AccessToken
from app.services.oauth.oauth_service import OauthService

PATCHED_MODULE = "app.services.api.http_service.request"
TARGET_AUDIENCE = "http://example.org/api"
TOKEN_EXPIRED = TOKEN_EXPIRES_IN + 1


@pytest.fixture
def mock_token_request_data() -> str:
    return urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "some_scope",
            "target_audience": TARGET_AUDIENCE,
        }
    )


@pytest.fixture
def mock_token_request_data_with_jwt() -> str:
    return urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "some_scope",
            "target_audience": TARGET_AUDIENCE,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": "jwt-token",
        }
    )


@pytest.fixture
def mock_token_response_body() -> Dict[str, Any]:
    return {
        "access_token": "some_value",
        "token_type": "Bearer",
        "scope": "some_scope",
    }


@pytest.fixture
def mock_oauth() -> OauthService:
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

    actual = mock_oauth.fetch_token(scope="some_scope", target_audience=TARGET_AUDIENCE)

    assert request.call_count == 1
    assert request.call_args[1]["method"] == "POST"
    assert request.call_args[1]["url"] == "http://example.org/oauth/token"
    assert request.call_args[1]["data"] == mock_token_request_data

    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.scope == mock_token_response_body["scope"]
    assert actual.target_audience == TARGET_AUDIENCE

    assert len(mock_oauth._tokens) == 1
    assert mock_oauth._tokens[0].access_token == mock_token_response_body["access_token"]


@patch(PATCHED_MODULE)
def test_do_request_should_reuse_token(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.append(
        AccessToken(
            access_token=mock_token_response_body["access_token"],
            token_type=mock_token_response_body["token_type"],
            scope=mock_token_response_body["scope"],
            target_audience=TARGET_AUDIENCE,
            added_at=int(time.time()),
        )
    )
    assert len(mock_oauth._tokens) == 1

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"], target_audience=TARGET_AUDIENCE)
    assert request.call_count == 0
    assert len(mock_oauth._tokens) == 1
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.scope == mock_token_response_body["scope"]


@patch(PATCHED_MODULE)
def test_do_request_should_request_new_token_if_expired(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.extend(
        [
            AccessToken(
                access_token="expired_token",
                token_type=mock_token_response_body["token_type"],
                scope=mock_token_response_body["scope"],
                target_audience=TARGET_AUDIENCE,
                added_at=int(time.time()) - TOKEN_EXPIRED,  # Expired token
            ),
            AccessToken(
                access_token="expired_token_2",
                token_type=mock_token_response_body["token_type"],
                scope=mock_token_response_body["scope"],
                target_audience=TARGET_AUDIENCE,
                added_at=int(time.time()) - TOKEN_EXPIRED,  # Expired token
            ),
            AccessToken(
                access_token="token_3",
                token_type=mock_token_response_body["token_type"],
                scope="different_scope",
                target_audience=TARGET_AUDIENCE,
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

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"], target_audience=TARGET_AUDIENCE)
    assert request.call_count == 1
    assert len(mock_oauth._tokens) == 2
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.scope == mock_token_response_body["scope"]
    for token in mock_oauth._tokens:
        assert token.is_expired is False


def test_token_has_scope_and_target_audience() -> None:
    token = AccessToken(
        access_token="test",
        token_type="Bearer",
        scope="read write admin",
        target_audience="http://example.org/api",
    )
    assert token.has_scope_and_target_audience("read", "http://example.org/api") is True
    assert token.has_scope_and_target_audience("read write", "http://example.org/api") is True
    assert token.has_scope_and_target_audience("read write admin", "http://example.org/api") is True
    assert token.has_scope_and_target_audience("delete", "http://example.org/api") is False
    assert token.has_scope_and_target_audience("read delete", "http://example.org/api") is False
    assert token.has_scope_and_target_audience("read", "http://other.org/api") is False


def test_mock_mode_returns_mock_token() -> None:
    """Test that mock mode returns a mock token without making requests."""
    oauth = OauthService(
        endpoint="http://example.org/oauth/token",
        timeout=1,
        mock=True,
    )

    token = oauth.fetch_token(scope="test_scope", target_audience=TARGET_AUDIENCE)

    assert token.access_token == "mock-access-token"
    assert token.token_type == "Bearer"
    assert token.scope == "test_scope"


@patch(PATCHED_MODULE)
def test_do_request_should_not_reuse_token_with_different_target_audience(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_oauth: OauthService,
) -> None:
    """Test that tokens are not reused when target_audience differs."""
    mock_oauth._tokens.append(
        AccessToken(
            access_token=mock_token_response_body["access_token"],
            token_type=mock_token_response_body["token_type"],
            scope=mock_token_response_body["scope"],
            target_audience="http://other.org/api",
            added_at=int(time.time()),
        )
    )
    assert len(mock_oauth._tokens) == 1

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"], target_audience=TARGET_AUDIENCE)

    assert request.call_count == 1
    assert len(mock_oauth._tokens) == 2
    assert actual.target_audience == TARGET_AUDIENCE
