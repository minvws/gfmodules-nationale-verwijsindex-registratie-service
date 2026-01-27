import logging
from typing import Any
from urllib.parse import urlencode


from app.models.token import AccessToken
from app.services.api.http_service import GfHttpService
from app.services.oauth.jwt_builder import JWTBuilder

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
        jwt_builder: JWTBuilder | None = None,
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
        self._jwt_builder = jwt_builder
        # Token cache
        self._tokens: list[AccessToken] = []

    def _add_data_if_ldn(self, data: dict[str, Any], scope: str, target_audience: str) -> None:
        logger.debug("Adding data if LDN certificate is used for mTLS")
        if self._jwt_builder is not None:
            token = self._jwt_builder.build(target_audience=target_audience, scope=scope)
            data["client_assertion_type"] = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            data["client_assertion"] = token

    def fetch_token(self, scope: str, target_audience: str) -> AccessToken:
        if self.mock:
            return AccessToken(
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

    def _get_valid_token(self, scope: str, target_audience: str) -> AccessToken | None:
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

    def _get_refreshable_token(self, scope: str, target_audience: str) -> AccessToken | None:
        """
        Returns expired token that can still be refreshed, else None
        """
        for token in reversed(self._tokens):
            if not token.has_scope_and_target_audience(scope, target_audience):
                continue
            if token.is_expired and token.can_refresh:
                return token
        return None

    def _refresh_token(self, token: AccessToken, target_audience: str) -> AccessToken:
        """
        Refreshes expired token with refresh token.
        """
        if token.refresh_token is None:
            raise ValueError("Cannot refresh token without refresh_token")

        logger.info(f"Refreshing OAuth token for scope: {token.scope}, target_audience: {target_audience}")
        new_token = self._call_oauth_api(
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "target_audience": target_audience,
            },
            target_audience=target_audience,
            scope=token.scope,
        )
        self._tokens.remove(token)
        logger.info(
            f"Successfully refreshed OAuth token for scope: {new_token.scope}, target_audience: {target_audience}"
        )
        return new_token

    def _get_new_token(self, scope: str, target_audience: str) -> AccessToken:
        """
        Requests a token from the oauth server for the given scope
        """
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
        """
        Calls the OAuth API to request a token with the given data
        """
        self._add_data_if_ldn(data, scope, target_audience)
        response = self._request_token(
            data=data,
            target_audience=target_audience,
        )
        self._tokens.append(response)
        return response

    def _request_token(self, data: dict[str, Any], target_audience: str) -> AccessToken:
        """
        Requests a token from the oauth server with the given data
        """
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
