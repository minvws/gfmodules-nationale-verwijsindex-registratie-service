import time
from typing import Any, Dict
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest

from app.models.token import TOKEN_EXPIRES_IN, AccessToken
from app.services.oauth.oauth_service import OauthService

PATCHED_MODULE = "app.services.api.http_service.request"
TARGET_AUDIENCE = "http://example.org/api"
ORG_URA = "12345678"
TOKEN_EXPIRED = TOKEN_EXPIRES_IN + 1


@pytest.fixture
def mock_token_request_data() -> str:
    return urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "some_scope",
            "target_audience": TARGET_AUDIENCE,
            "org_ura": ORG_URA,
        }
    )


@pytest.fixture
def mock_token_response_body() -> Dict[str, Any]:
    return {
        "access_token": "some_value",
        "scope": "some_scope",
    }


@pytest.fixture
def mock_oauth() -> OauthService:
    return OauthService(
        endpoint="http://example.org/oauth",
        timeout=1,
        org_register_id=ORG_URA,
        target_audience=TARGET_AUDIENCE,
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
    assert request.call_args[1]["url"] == "http://example.org/oauth/token"  # endpoint + "token" sub_route
    assert request.call_args[1]["data"] == mock_token_request_data

    assert actual.access_token == mock_token_response_body["access_token"]
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
        AccessToken(
            access_token=mock_token_response_body["access_token"],
            scope=mock_token_response_body["scope"],
            added_at=int(time.time()),
        )
    )
    assert len(mock_oauth._tokens) == 1

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])
    assert request.call_count == 0
    assert len(mock_oauth._tokens) == 1
    assert actual.access_token == mock_token_response_body["access_token"]
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
                scope=mock_token_response_body["scope"],
                added_at=int(time.time()) - TOKEN_EXPIRED,  # Expired token
            ),
            AccessToken(
                access_token="token_3",
                scope="different_scope",
                added_at=int(time.time()),
            ),
        ]
    )
    assert mock_oauth._tokens[0].is_expired is True

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = mock_token_response_body
    request.return_value = mock_token_response

    actual = mock_oauth.fetch_token(scope=mock_token_response_body["scope"])
    assert request.call_count == 1
    assert actual.access_token == mock_token_response_body["access_token"]
    assert actual.scope == mock_token_response_body["scope"]
    for token in mock_oauth._tokens:
        assert token.is_expired is False


def test_token_has_scope() -> None:
    token = AccessToken(
        access_token="test",
        scope="read write admin",
    )
    assert token.has_scope("read") is True
    assert token.has_scope("read write") is True
    assert token.has_scope("read write admin") is True
    assert token.has_scope("delete") is False
    assert token.has_scope("read delete") is False


def test_mock_mode_returns_mock_token() -> None:
    """Test that mock mode returns a mock token without making requests."""
    oauth = OauthService(
        endpoint="http://example.org/oauth",
        timeout=1,
        org_register_id=ORG_URA,
        target_audience=TARGET_AUDIENCE,
        mock=True,
    )

    token = oauth.fetch_token(scope="test_scope")

    assert token.access_token == "mock-access-token"
    assert token.scope == "test_scope"
