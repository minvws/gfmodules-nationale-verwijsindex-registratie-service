import time
from typing import List
from urllib.parse import urlencode
from pydantic import BaseModel, Field
from app.services.api.http_service import GfHttpService

import logging

logger = logging.getLogger(__name__)


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: List[str]
    added_at: int | None = Field(default_factory=lambda: int(time.time()))

    @property
    def is_expired(self) -> bool:
        if self.added_at is None:
            return True
        return (self.added_at + self.expires_in) <= int(time.time())


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

    def fetch_token(self, scope: str) -> Token:
        if self.mock:
            return Token(
                access_token="mock-access-token",
                token_type="Bearer",
                expires_in=999999,
                scope=[scope],
            )
        logger.info(f"Fetching OAuth token for scope: {scope}")
        token = self._get_last_token(scope=scope)
        if token is None:
            token = self._get_new_token(scope=scope)
        return token

    def _clear_expired_tokens(self) -> None:
        """
        Clears all expired tokens from the token list
        """
        logger.info("Clearing expired OAuth tokens")
        self._tokens = [token for token in self._tokens if token.is_expired is False]

    def _get_last_token(self, scope: str) -> Token | None:
        """
        Gets the last unexpired token with the given scope.
        If no token is available, return None
        """
        if not self._tokens:
            return None
        self._clear_expired_tokens()
        for token in reversed(self._tokens):
            if scope not in token.scope:
                continue
            if token.added_at is None:
                continue
            if (token.added_at + token.expires_in) > int(time.time()):
                logger.info(f"Reusing existing OAuth token for scope: {scope}")
                return token
        return None

    def _get_new_token(self, scope: str) -> Token:
        """
        Requests a new token from the token endpoint
        """
        logger.info(f"Requesting new OAuth token for scope: {scope}")
        response = self._http_service.do_request(
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=urlencode(
                {
                    "grant_type": "client_credentials",
                    "scope": scope,
                }
            ),
        )
        response.raise_for_status()
        token = Token(**response.json())
        self._tokens.append(token)
        return token
