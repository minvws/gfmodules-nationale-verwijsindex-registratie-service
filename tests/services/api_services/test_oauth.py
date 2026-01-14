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
            "target_audience": "http://example.org/api",
        }
    )


@pytest.fixture
def mock_refresh_token_request_data() -> str:
    return urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": "some_refresh_value",
            "target_audience": "http://example.org/api",
        }
    )


@pytest.fixture
def mock_token_response_body() -> Dict[str, Any]:
    return {
        "access_token": "some_value",
        "token_type": "Bearer",
        "scope": ["some_scope"],
        "refresh_token": "some_refresh_value",
    }


@pytest.fixture
def mock_refreshed_token_response_body() -> Dict[str, Any]:
    return {
        "access_token": "new_refreshed_token",
        "token_type": "Bearer",
        "scope": ["some_scope"],
        "refresh_token": "new_refresh_value",
    }


@pytest.fixture
def mock_oauth(
    http_service: HttpService,
) -> OauthService:
    return OauthService(
        endpoint="http://example.org/oauth/token",
        timeout=1,
        target_audience="http://example.org/api",
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

    actual = mock_oauth.fetch_token(scope=["some_scope"])

    assert request.call_count == 1
    assert request.call_args[1]["method"] == "POST"
    assert request.call_args[1]["url"] == "http://example.org/oauth/token"
    assert request.call_args[1]["data"] == mock_token_request_data

    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
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
            scope=mock_token_response_body["scope"],
            added_at=int(time.time()),
        )
    )
    assert len(mock_oauth._tokens) == 1

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])
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
            Token(
                access_token="expired_token",
                token_type=mock_token_response_body["token_type"],
                scope=mock_token_response_body["scope"],
                added_at=int(time.time()) - 4000,
            ),
            Token(
                access_token="expired_token_2",
                token_type=mock_token_response_body["token_type"],
                scope=mock_token_response_body["scope"],
                added_at=int(time.time()) - 4000,
            ),
            Token(
                access_token="token_3",
                token_type=mock_token_response_body["token_type"],
                scope=["different_scope"],
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

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])
    assert request.call_count == 1
    assert len(mock_oauth._tokens) == 2
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.token_type == mock_token_response_body["token_type"]
    assert actual.scope == mock_token_response_body["scope"]
    for token in mock_oauth._tokens:
        assert token.is_expired is False

@patch(PATCHED_MODULE)
def test_do_request_should_refresh_expired_token_with_refresh_token(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_refreshed_token_response_body: Dict[str, Any],
    mock_refresh_token_request_data: str,
    mock_oauth: OauthService,
) -> None:
    """Test that an expired token with a valid refresh token gets refreshed."""
    mock_oauth._tokens.append(
        Token(
            access_token="expired_token",
            token_type=mock_token_response_body["token_type"],
            scope=mock_token_response_body["scope"],
            refresh_token="some_refresh_value",
            added_at=int(time.time()) - 100,  # Expired but refresh token still valid
        )
    )
    assert mock_oauth._tokens[0].is_expired is True
    assert mock_oauth._tokens[0].can_refresh is True
    assert len(mock_oauth._tokens) == 1

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_refreshed_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])

    assert request.call_count == 1
    assert request.call_args[1]["method"] == "POST"
    assert request.call_args[1]["data"] == mock_refresh_token_request_data

    assert len(mock_oauth._tokens) == 1
    assert actual.access_token == mock_refreshed_token_response_body["access_token"]
    assert actual.refresh_token == mock_refreshed_token_response_body["refresh_token"]


@patch(PATCHED_MODULE)
def test_do_request_should_get_new_token_if_refresh_token_expired(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_token_request_data: str,
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.append(
        Token(
            access_token="expired_token",
            token_type=mock_token_response_body["token_type"],
            scope=mock_token_response_body["scope"],
            refresh_token="expired_refresh_token",
            added_at=int(time.time()) - 4000,  # Both token and refresh token expired
        )
    )
    assert mock_oauth._tokens[0].is_expired is True
    assert mock_oauth._tokens[0].is_refresh_token_expired is True
    assert mock_oauth._tokens[0].can_refresh is False

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])

    assert request.call_count == 1
    assert request.call_args[1]["data"] == mock_token_request_data
    assert "grant_type=client_credentials" in request.call_args[1]["data"]

    assert actual.access_token == mock_token_response_body["access_token"]


@patch(PATCHED_MODULE)
def test_do_request_should_get_new_token_if_no_refresh_token(
    request: MagicMock,
    mock_token_response_body: Dict[str, Any],
    mock_token_request_data: str,
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.append(
        Token(
            access_token="expired_token",
            token_type=mock_token_response_body["token_type"],
            scope=mock_token_response_body["scope"],
            refresh_token=None,
            added_at=int(time.time()) - 100,
        )
    )
    assert mock_oauth._tokens[0].is_expired is True
    assert mock_oauth._tokens[0].can_refresh is False

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])

    assert request.call_count == 1
    assert "grant_type=client_credentials" in request.call_args[1]["data"]
    assert actual.access_token == mock_token_response_body["access_token"]

def test_token_has_scope() -> None:
    token = Token(
        access_token="test",
        token_type="Bearer",
        scope=["read", "write", "admin"],
    )
    assert token.has_scope(["read"]) is True
    assert token.has_scope(["read", "write"]) is True
    assert token.has_scope(["read", "write", "admin"]) is True
    assert token.has_scope(["delete"]) is False
    assert token.has_scope(["read", "delete"]) is False

def test_token_can_refresh() -> None:
    token_no_refresh = Token(
        access_token="test",
        token_type="Bearer",
        scope=["test"],
        refresh_token=None,
    )
    assert token_no_refresh.can_refresh is False

    token_with_refresh = Token(
        access_token="test",
        token_type="Bearer",
        scope=["test"],
        refresh_token="refresh_token_value",
        added_at=int(time.time()),
    )
    assert token_with_refresh.can_refresh is True

    token_expired_refresh = Token(
        access_token="test",
        token_type="Bearer",
        scope=["test"],
        refresh_token="refresh_token_value",
        added_at=int(time.time()) - 4000,  # Refresh token expired
    )
    assert token_expired_refresh.can_refresh is False


@patch(PATCHED_MODULE)
def test_clear_expired_tokens_keeps_refreshable_tokens(
    request: MagicMock,
    mock_oauth: OauthService,
) -> None:
    mock_oauth._tokens.extend(
        [
            Token(
                access_token="expired_no_refresh",
                token_type="Bearer",
                scope=["scope1"],
                refresh_token=None,
                added_at=int(time.time()) - 100,
            ),
            Token(
                access_token="expired_with_refresh",
                token_type="Bearer",
                scope=["scope2"],
                refresh_token="refresh_value",
                added_at=int(time.time()) - 100,  # Expired but can refresh
            ),
            Token(
                access_token="valid_token",
                token_type="Bearer",
                scope=["scope3"],
                added_at=int(time.time()),
            ),
        ]
    )

    mock_oauth._clear_expired_tokens()

    assert len(mock_oauth._tokens) == 2
    access_tokens = [t.access_token for t in mock_oauth._tokens]
    assert "expired_no_refresh" not in access_tokens
    assert "expired_with_refresh" in access_tokens
    assert "valid_token" in access_tokens


def test_mock_mode_returns_mock_token() -> None:
    """Test that mock mode returns a mock token without making requests."""
    oauth = OauthService(
        endpoint="http://example.org/oauth/token",
        timeout=1,
        target_audience="http://example.org/api",
        mock=True,
    )

    token = oauth.fetch_token(scope=["test_scope"])

    assert token.access_token == "mock-access-token"
    assert token.token_type == "Bearer"
    assert token.scope == ["test_scope"]
