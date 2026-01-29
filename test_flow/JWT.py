import base64
import hashlib
import re
import time
import uuid
from typing import Any, Dict, List, Optional

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from uzireader.uziserver import UziServer
from cryptography.hazmat.primitives.asymmetric import rsa

AllowedPrivateKeys = rsa.RSAPrivateKey


class JWTBuilder:
    """
    Utility to generate a client_assertion JWT for OAuth2 client_credentials.
    """

    def __init__(
        self,
        token_url: str,
        mtls_cert_path: str,
        signing_cert_path: str,
        signing_key_path: str,
    ) -> None:
        self.token_url = token_url
        self.mtls_cert_path = mtls_cert_path
        self.signing_cert_path = signing_cert_path
        self.signing_key_path = signing_key_path

    @staticmethod
    def b64url_nopad(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

    @staticmethod
    def load_cert_pem(path: str) -> x509.Certificate:
        with open(path, "rb") as f:
            data = f.read()
        return x509.load_pem_x509_certificate(data)

    @staticmethod
    def split_certificates(pem_bundle: str) -> List[str]:
        """Return each certificate block found in a concatenated PEM bundle."""

        _CERT_PATTERN = re.compile(
            r"-----BEGIN CERTIFICATE-----\s.+?-----END CERTIFICATE-----",
            re.DOTALL,
        )
        return [match.strip() for match in _CERT_PATTERN.findall(pem_bundle)]

    @staticmethod
    def load_cert_pem_bundle(path: str) -> List[x509.Certificate]:
        with open(path, "r", encoding="utf-8") as f:
            pem_bundle = f.read()
        certs_pem = JWTBuilder.split_certificates(pem_bundle)
        certs = [
            x509.load_pem_x509_certificate(cert.encode("utf-8")) for cert in certs_pem
        ]
        return certs

    @staticmethod
    def load_private_key_pem(path: str, password: Optional[str]) -> AllowedPrivateKeys:
        with open(path, "rb") as f:
            key_bytes = f.read()
        pw = password.encode("utf-8") if password else None
        key = serialization.load_pem_private_key(key_bytes, password=pw)
        if not isinstance(key, AllowedPrivateKeys):
            raise ValueError("Unsupported private key type.")
        return key

    @staticmethod
    def cert_thumbprint_x5t_s256(cert: x509.Certificate) -> str:
        der = cert.public_bytes(serialization.Encoding.DER)
        digest = hashlib.sha256(der).digest()
        return JWTBuilder.b64url_nopad(digest)

    @staticmethod
    def cert_to_x5c_b64(cert: x509.Certificate) -> str:
        der = cert.public_bytes(serialization.Encoding.DER)
        return base64.b64encode(der).decode("ascii")

    def build(
        self,
        scope: Optional[str],
        target_audience: Optional[str],
        expires_in: int = 300,
        include_x5c: bool = True,
        signing_key_password: Optional[str] = None,
    ) -> str:
        mtls_cert = self.load_cert_pem(self.mtls_cert_path)
        mtls_x5t_s256 = self.cert_thumbprint_x5t_s256(mtls_cert)

        if not (self.signing_cert_path and self.signing_key_path):
            raise ValueError("Provide signing_cert_path and signing_key_path.")
        cert_chain: List[x509.Certificate] = self.load_cert_pem_bundle(self.signing_cert_path)
        signing_cert = cert_chain[0]
        signing_key = self.load_private_key_pem(
            self.signing_key_path, password=signing_key_password
        )

        with open(self.signing_cert_path, "r", encoding="utf-8") as f:
            cert_pem = f.read()
        uzi_data = UziServer(verify="SUCCESS", cert=cert_pem)
        ura_number = uzi_data["SubscriberNumber"]

        alg = "RS256"
        now = int(time.time())
        jti = str(uuid.uuid4())

        claims = {
            "iss": ura_number,
            "sub": ura_number,
            "aud": self.token_url,
            "scope": scope,
            "target_audience": target_audience,
            "iat": now,
            "exp": now + int(expires_in),
            "jti": jti,
            "cnf": {"x5t#S256": mtls_x5t_s256},
        }

        header: Dict[str, Any] = {
            "typ": "JWT",
            "alg": alg,
            "kid": self.cert_thumbprint_x5t_s256(signing_cert),
        }
        if include_x5c:
            header["x5c"] = [self.cert_to_x5c_b64(c) for c in cert_chain]

        token = jwt.encode(
            payload=claims,
            key=signing_key,
            algorithm=alg,
            headers=header,
        )
        print(token)

        if isinstance(token, bytes):
            token = token.decode("ascii")

        return token
