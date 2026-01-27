from app.models.ura_number import UraNumber
from typing import Any

import time
import uuid
import jwt
import hashlib

import base64
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed448, ed25519, rsa
import logging

JWTSigningKey = rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey | ed25519.Ed25519PrivateKey | ed448.Ed448PrivateKey


TOKEN_REQUEST_JWT_EXPIRES_IN = 1800  # 30 minutes

logger = logging.getLogger(__name__)


class JWTBuilder:
    def __init__(
        self,
        endpoint: str,
        mtls_cert: str,
        ura_number: UraNumber,
        jwt_signing_cert: str,
        jwt_signing_key: str,
        include_x5c: bool,
    ):
        self._endpoint = endpoint
        self._ura_number = ura_number
        self._mtls_x5t_s256 = self._cert_thumbprint_x5t_s256(self._load_cert_pem(mtls_cert))
        self._jwt_signing_key = self._load_private_key_pem(jwt_signing_key, password=None)
        jwt_cert_pem = self._load_cert_pem(jwt_signing_cert)
        self._jwt_signing_x5t_s256 = self._cert_thumbprint_x5t_s256(jwt_cert_pem)

        if include_x5c:
            self._x5c_chain = [self._cert_to_x5c_b64(jwt_cert_pem)]
        else:
            self._x5c_chain = []

    def build(self, target_audience: str, scope: str) -> str:
        now = int(time.time())
        exp = now + TOKEN_REQUEST_JWT_EXPIRES_IN
        alg = "RS256"

        claims = {
            "iss": str(self._ura_number),
            "sub": str(self._ura_number),
            "aud": self._endpoint,
            "scope": scope,
            "target_audience": target_audience,
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
            "cnf": {"x5t#S256": self._mtls_x5t_s256},
        }

        header: dict[str, Any] = {
            "typ": "JWT",
            "alg": alg,
            "kid": self._jwt_signing_x5t_s256,
        }
        if self._x5c_chain:
            header["x5c"] = self._x5c_chain

        return jwt.encode(payload=claims, key=self._jwt_signing_key, algorithm=alg, headers=header)

    def _load_private_key_pem(self, path: str, password: str | None = None) -> JWTSigningKey:
        with open(path, "rb") as f:
            key_bytes = f.read()
        pw = password.encode("utf-8") if password else None
        key = serialization.load_pem_private_key(key_bytes, password=pw)
        if not isinstance(key, JWTSigningKey):
            raise ValueError("Unsupported private key type")
        return key

    def _load_cert_pem(self, path: str) -> x509.Certificate:
        with open(path, "rb") as f:
            data = f.read()
        return x509.load_pem_x509_certificate(data)

    def _cert_thumbprint_x5t_s256(self, cert: x509.Certificate) -> str:
        der = cert.public_bytes(serialization.Encoding.DER)
        digest = hashlib.sha256(der).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    def _cert_to_x5c_b64(self, cert: x509.Certificate) -> str:
        der = cert.public_bytes(serialization.Encoding.DER)
        return base64.b64encode(der).decode("ascii")
