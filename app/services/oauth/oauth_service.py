import logging
from urllib.parse import urlencode


from app.models.token import AccessToken
from app.services.api.http_service import GfHttpService

logger = logging.getLogger(__name__)


class OauthService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        org_register_id: str,
        target_audience: str,
        mock: bool = False,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ca: str | bool = True,
        source_id: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ):
        self._endpoint = endpoint
        self.mock = mock
        self._http_service = GfHttpService(
            endpoint=self._endpoint,
            timeout=timeout,
            mtls_cert=mtls_cert,
            mtls_key=mtls_key,
            verify_ca=verify_ca,
            extra_headers=extra_headers,
        )
        self._org_register_id = org_register_id
        self._source_id = source_id
        self._target_audience = target_audience
        self._tokens: list[AccessToken] = []

    def fetch_token(self, scope: str) -> AccessToken:
        try:
            if self.mock:
                return AccessToken(
                    access_token="mock-access-token",
                    scope=scope,
                )
            logger.info(f"Fetching OAuth token for scope: {scope}")

            token = self._get_cached_token(scope=scope)
            if token is not None:
                return token

            return self._request_new_token(scope)
        except Exception:
            logger.exception("Failed to fetch OAuth token")
            raise

    def _clear_expired_tokens(self) -> None:
        self._tokens = [token for token in self._tokens if not token.is_expired]

    def _get_cached_token(self, scope: str) -> AccessToken | None:
        if not self._tokens:
            return None

        self._clear_expired_tokens()

        for token in reversed(self._tokens):
            if not token.has_scope(scope):
                continue
            if not token.is_expired:
                logger.info(f"Reusing existing OAuth token for scope: {scope}")
                return token
        return None

    def _request_new_token(self, scope: str) -> AccessToken:
        data = {
            "grant_type": "client_credentials",
            "scope": scope,
            "target_audience": self._target_audience,
        }
        if self._source_id:
            data["source_id"] = self._source_id
        if len(self._org_register_id) > 8:
            data["org_oin"] = self._org_register_id
        else:
            data["org_ura"] = self._org_register_id

        logger.debug(f"Requesting token with data: {data}")
        try:
            response = self._http_service.do_request(
                method="POST",
                sub_route="token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=urlencode(data),
            )
            response.raise_for_status()
        except Exception:
            logger.exception("Failed to obtain OAuth token")
            raise
        token = AccessToken(**response.json())
        self._tokens.append(token)
        return token
