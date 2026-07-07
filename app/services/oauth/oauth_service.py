import logging
from typing import Any
from urllib.parse import urlencode


from app.models.token import AccessToken
from app.services.api.http_service import GfHttpService

logger = logging.getLogger(__name__)


TOKEN_REQUEST_JWT_EXPIRES_IN = 1800  # 30 minutes


class OauthService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mock: bool = False,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ca: str | bool = True,
    ):
        self._endpoint = endpoint
        self.mock = mock
        self._http_service = GfHttpService(
            endpoint=self._endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
        )
        # Token cache
        self._tokens: list[AccessToken] = []

    def fetch_token(self, scope: str, target_audience: str) -> AccessToken:
        if self.mock:
            return AccessToken(
                access_token="mock-access-token",
                token_type="Bearer",
                scope=scope,
                target_audience=target_audience,
            )
        logger.info(f"Fetching OAuth token for scope: {scope}, target_audience: {target_audience}")

        token = self._get_valid_token(scope=scope, target_audience=target_audience)
        if token is not None:
            return token

        return self._get_new_token(scope=scope, target_audience=target_audience)

    def _clear_expired_tokens(self) -> None:
        self._tokens = [token for token in self._tokens if not token.is_expired]

    def _get_valid_token(self, scope: str, target_audience: str) -> AccessToken | None:
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

    def _get_new_token(self, scope: str, target_audience: str) -> AccessToken:
        logger.info(f"Requesting new OAuth token for scope: {scope}, target_audience: {target_audience}")
        token = self._call_oauth_api(
            data={
                "grant_type": "client_credentials",
                "scope": scope,
                "target_audience": target_audience,
            },
            target_audience=target_audience,
            scope=scope,
        )
        logger.info(f"New OAuth token for scope: {scope}, target_audience: {target_audience}")
        return token

    def _call_oauth_api(self, data: dict[str, Any], target_audience: str, scope: str) -> AccessToken:
        response = self._request_token(
            data=data,
            target_audience=target_audience,
            scope=scope,
        )
        self._tokens.append(response)
        return response

    def _request_token(self, data: dict[str, Any], target_audience: str, scope: str) -> AccessToken:
        logger.debug(f"Requesting token with data: {data}")
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
        return AccessToken(**response.json(), target_audience=target_audience)
