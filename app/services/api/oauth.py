import logging
import time
from typing import Any, Dict, List
from urllib.parse import urlencode

from pydantic import BaseModel, Field

from app.services.api.http_service import GfHttpService

logger = logging.getLogger(__name__)


TOKEN_EXPIRES_IN = 600  # 10 minutes
REFRESH_TOKEN_EXPIRES_IN = 3600  # 1 hour
TOKEN_EXPIRY_BUFFER = 30  # Refresh token 30 seconds before expiry


class Token(BaseModel):
    access_token: str
    token_type: str
    scope: List[str]
    refresh_token: str | None = None
    expires_in: int | None = None
    added_at: int = Field(default_factory=lambda: int(time.time()))
    target_audience: str | None = None

    def has_scope_and_target_audience(self, scope: List[str], target_audience: str) -> bool:
        """
        Checks if this token has all the requested scopes and matches the target audience.
        """
        return all(s in self.scope for s in scope) and self.target_audience == target_audience

    @property
    def is_expired(self) -> bool:
        expires_in = self.expires_in or TOKEN_EXPIRES_IN
        return (self.added_at + expires_in - TOKEN_EXPIRY_BUFFER) <= int(time.time())

    @property
    def is_refresh_token_expired(self) -> bool:
        if self.refresh_token is None:
            return True
        return (self.added_at + REFRESH_TOKEN_EXPIRES_IN - TOKEN_EXPIRY_BUFFER) <= int(time.time())

    @property
    def can_refresh(self) -> bool:
        return self.refresh_token is not None and not self.is_refresh_token_expired


class OauthService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ca: str | bool = True,
        mock: bool = False,
    ):
        self._http_service = GfHttpService(
            endpoint=endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
        )
        self._tokens: List[Token] = []
        self.mock = mock

    def fetch_token(self, scope: List[str], target_audience: str) -> Token:
        if self.mock:
            return Token(
                access_token="mock-access-token",
                token_type="Bearer",
                scope=scope,
            )
        logger.info(f"Fetching OAuth token for scope: {scope}, target_audience: {target_audience}")

        token = self._get_valid_token(scope=scope, target_audience=target_audience)
        if token is not None:
            return token

        refreshable_token = self._get_refreshable_token(scope=scope, target_audience=target_audience)
        if refreshable_token is not None:
            return self._refresh_token(refreshable_token, target_audience=target_audience)

        return self._get_new_token(scope=scope, target_audience=target_audience)

    def _clear_expired_tokens(self) -> None:
        """
        Clears all tokens that are expired and cannot be refreshed.
        """
        self._tokens = [token for token in self._tokens if not token.is_expired or token.can_refresh]

    def _get_valid_token(self, scope: List[str], target_audience: str) -> Token | None:
        """
        Gets a non-expired token with the given scope, else None
        """
        if not self._tokens:
            return None

        self._clear_expired_tokens()

        for token in reversed(self._tokens):
            if not token.has_scope_and_target_audience(scope, target_audience):
                continue
            if not token.is_expired:
                logger.info(f"Reusing existing OAuth token for scope: {scope}, target_audience: {target_audience}")
                return token
        return None

    def _get_refreshable_token(self, scope: List[str], target_audience: str) -> Token | None:
        """
        Returns expired token that can still be refreshed, else None
        """
        for token in reversed(self._tokens):
            if not token.has_scope_and_target_audience(scope, target_audience):
                continue
            if token.is_expired and token.can_refresh:
                return token
        return None

    def _refresh_token(self, token: Token, target_audience: str) -> Token:
        """
        Refreshes expired token with refresh token.
        """
        if token.refresh_token is None:
            raise ValueError("Cannot refresh token without refresh_token")

        logger.info(f"Refreshing OAuth token for scope: {token.scope}, target_audience: {target_audience}")
        new_token = self._request_token(
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "target_audience": target_audience,
            },
            target_audience=target_audience,
        )
        self._tokens.remove(token)
        logger.info(
            f"Successfully refreshed OAuth token for scope: {new_token.scope}, target_audience: {target_audience}"
        )
        return new_token

    def _get_new_token(self, scope: List[str], target_audience: str) -> Token:
        """
        Requests a token from the oauth server for the given scope
        """
        scope_str = " ".join(scope)
        logger.info(f"Requesting new OAuth token for scope: {scope}, target_audience: {target_audience}")
        token = self._request_token(
            data={
                "grant_type": "client_credentials",
                "scope": scope_str,
                "target_audience": target_audience,
            },
            target_audience=target_audience,
        )
        logger.info(f"New OAuth token for scope: {scope}, target_audience: {target_audience}")
        return token

    def _request_token(self, data: Dict[str, Any], target_audience: str) -> Token:
        """
        Requests a token from the oauth server with the given data
        """
        try:
            response = self._http_service.do_request(
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=urlencode(data),
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to obtain OAuth token: {e}")
            raise
        token = Token(**response.json(), target_audience=target_audience)
        self._tokens.append(token)
        return token
