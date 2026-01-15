import logging
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import jwt
from cryptography import x509
from jwt.algorithms import AllowedPrivateKeys
from pydantic import BaseModel, Field

from app.models.ura_number import UraNumber
from app.services.api.http_service import GfHttpService
from app.services.api.utils import (
    cert_thumbprint_x5t_s256,
    cert_to_x5c_b64,
    is_uzi_cert,
    load_cert_pem,
    load_private_key_pem,
)
from app.services.ura import UraNumberService

logger = logging.getLogger(__name__)


TOKEN_EXPIRES_IN = 600  # 10 minutes
REFRESH_TOKEN_EXPIRES_IN = 3600  # 1 hour
TOKEN_EXPIRY_BUFFER = 30  # Refresh token 30 seconds before expiry
TOKEN_REQUEST_JWT_EXPIRES_IN = 1800  # 30 minutes


class Token(BaseModel):
    access_token: str
    token_type: str
    scope: str
    refresh_token: str | None = None
    expires_in: int | None = None
    added_at: int = Field(default_factory=lambda: int(time.time()))
    target_audience: str | None = None

    def has_scope_and_target_audience(self, scope: str, target_audience: str) -> bool:
        """
        Checks if this token has all the requested scopes and matches the target audience.
        """
        token_scopes = self.scope.split()
        requested_scopes = scope.split()
        return all(s in token_scopes for s in requested_scopes) and self.target_audience == target_audience

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


class JWTData(BaseModel):
    jwt: str
    expires_at: int


class OauthService:
    def __init__(
        self,
        endpoint: str,
        timeout: int,
        mock: bool = False,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ca: str | bool = True,
        uzi_cert_path: str | None = None,
        uzi_key_path: str | None = None,
        include_x5c: bool = True,
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

        # mTLS certificate (can be either LDN or UZI cert)
        self._mtls_cert = mtls_cert
        self._mtls_is_uzi: bool | None = None

        # JWT signing configuration (UZI cert for signing client assertions)
        self._uzi_cert_path = uzi_cert_path
        self._uzi_key_path = uzi_key_path
        self._jwt_signing_cert: x509.Certificate | None = None
        self._jwt_signing_key: AllowedPrivateKeys | None = None
        self._mtls_x5t_s256: str | None = None
        self._jwt_signing_x5t_s256: str | None = None
        self._ura_number: UraNumber | None = None
        self._include_x5c = include_x5c
        self._x5c_chain: list[str] | None = None

        # Token cache
        self._tokens: list[Token] = []
        self._jwt: JWTData | None = None

    @property
    def mtls_is_uzi(self) -> bool:
        if self._mtls_is_uzi is None:
            self._mtls_is_uzi = is_uzi_cert(self._mtls_cert) if self._mtls_cert else False
        return self._mtls_is_uzi

    @property
    def mtls_x5t_s256(self) -> str | None:
        if self._mtls_x5t_s256 is None and self._mtls_cert:
            self._mtls_x5t_s256 = cert_thumbprint_x5t_s256(load_cert_pem(self._mtls_cert))
        return self._mtls_x5t_s256

    @property
    def jwt_signing_cert(self) -> x509.Certificate | None:
        if self._jwt_signing_cert is None and self._uzi_cert_path:
            self._jwt_signing_cert = load_cert_pem(self._uzi_cert_path)
        return self._jwt_signing_cert

    @property
    def jwt_signing_key(self) -> AllowedPrivateKeys | None:
        if self._jwt_signing_key is None and self._uzi_key_path:
            self._jwt_signing_key = load_private_key_pem(self._uzi_key_path, password=None)
        return self._jwt_signing_key

    @property
    def jwt_signing_x5t_s256(self) -> str | None:
        if self._jwt_signing_x5t_s256 is None and self.jwt_signing_cert:
            self._jwt_signing_x5t_s256 = cert_thumbprint_x5t_s256(self.jwt_signing_cert)
        return self._jwt_signing_x5t_s256

    @property
    def ura_number(self) -> UraNumber | None:
        if self._ura_number is None and self._uzi_cert_path:
            self._ura_number = UraNumberService.get_ura_number(self._uzi_cert_path)
        return self._ura_number

    @property
    def x5c_chain(self) -> list[str]:
        if self._x5c_chain is None:
            if self._include_x5c and self.jwt_signing_cert:
                self._x5c_chain = [cert_to_x5c_b64(self.jwt_signing_cert)]
            else:
                self._x5c_chain = []
        return self._x5c_chain

    def _get_or_create_jwt(self, target_audience: str, scope: str) -> JWTData:
        if self._jwt is None or time.time() >= self._jwt.expires_at:
            self._jwt = self._build_jwt_request_token(target_audience=target_audience, scope=scope)
        return self._jwt

    def _build_jwt_request_token(self, target_audience: str, scope: str) -> JWTData:
        if self.ura_number is None:
            raise ValueError("URA number is not set")
        if self.mtls_x5t_s256 is None:
            raise ValueError("mTLS certificate thumbprint is not set")
        if self.jwt_signing_x5t_s256 is None:
            raise ValueError("JWT signing certificate thumbprint is not set")
        if self.jwt_signing_key is None:
            raise ValueError("JWT signing key is not set")

        now = int(time.time())
        exp = now + TOKEN_REQUEST_JWT_EXPIRES_IN
        alg = "RS256"

        claims = {
            "iss": str(self.ura_number),
            "sub": str(self.ura_number),
            "aud": self._endpoint,
            "scope": scope,
            "target_audience": target_audience,
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
            "cnf": {"x5t#S256": self.mtls_x5t_s256},
        }

        header: dict[str, Any] = {
            "typ": "JWT",
            "alg": alg,
            "kid": self.jwt_signing_x5t_s256,
        }
        if self.x5c_chain:
            header["x5c"] = self.x5c_chain

        token = jwt.encode(payload=claims, key=self.jwt_signing_key, algorithm=alg, headers=header)
        return JWTData(jwt=token, expires_at=exp)

    def _add_data_if_ldn(self, data: dict[str, Any], scope: str, target_audience: str) -> None:
        if not self.mtls_is_uzi:
            data["client_assertion_type"] = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
            data["client_assertion"] = self._get_or_create_jwt(target_audience=target_audience, scope=scope).jwt

    def fetch_token(self, scope: str, target_audience: str) -> Token:
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

    def _get_valid_token(self, scope: str, target_audience: str) -> Token | None:
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

    def _get_refreshable_token(self, scope: str, target_audience: str) -> Token | None:
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
            scope=token.scope,
        )
        self._tokens.remove(token)
        logger.info(
            f"Successfully refreshed OAuth token for scope: {new_token.scope}, target_audience: {target_audience}"
        )
        return new_token

    def _get_new_token(self, scope: str, target_audience: str) -> Token:
        """
        Requests a token from the oauth server for the given scope
        """
        logger.info(f"Requesting new OAuth token for scope: {scope}, target_audience: {target_audience}")
        token = self._request_token(
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

    def _request_token(self, data: dict[str, Any], target_audience: str, scope: str) -> Token:
        """
        Requests a token from the oauth server with the given data
        """
        self._add_data_if_ldn(data, scope=scope, target_audience=target_audience)
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
