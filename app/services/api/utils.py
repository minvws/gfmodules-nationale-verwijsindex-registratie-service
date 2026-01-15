import hashlib

import base64
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from jwt.algorithms import AllowedPrivateKeys
from uzireader.uziserver import UziServer

import logging

logger = logging.getLogger(__name__)

def b64url_nopad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def load_private_key_pem(path: str, password: str | None = None) -> AllowedPrivateKeys:
    with open(path, "rb") as f:
        key_bytes = f.read()
    pw = password.encode("utf-8") if password else None
    key = serialization.load_pem_private_key(key_bytes, password=pw)
    if not isinstance(key, AllowedPrivateKeys):
        raise ValueError("Unsupported private key type")
    return key


def load_cert_pem(path: str) -> x509.Certificate:
    with open(path, "rb") as f:
        data = f.read()
    return x509.load_pem_x509_certificate(data)


def cert_thumbprint_x5t_s256(cert: x509.Certificate) -> str:
    der = cert.public_bytes(serialization.Encoding.DER)
    digest = hashlib.sha256(der).digest()
    return b64url_nopad(digest)


def cert_to_x5c_b64(cert: x509.Certificate) -> str:
    der = cert.public_bytes(serialization.Encoding.DER)
    return base64.b64encode(der).decode("ascii")

def is_uzi_cert(cert_path: str) -> bool:
    with open(cert_path, "r", encoding="utf-8") as f:
        cert_pem = f.read()
    UziServer(verify="SUCCESS", cert=cert_pem)
    return True