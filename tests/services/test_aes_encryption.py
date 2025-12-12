import base64
import os
from unittest.mock import patch, MagicMock

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.aes_encryption_service import AesEncryptionService, AesEncryptionError


@pytest.fixture
def encryption_service() -> AesEncryptionService:
    key = AESGCM.generate_key(bit_length=128)
    return AesEncryptionService(key=key)


def test_encrypt_decrypt(encryption_service: AesEncryptionService) -> None:
    plaintext = "patient-12345"
    token = encryption_service.encrypt(plaintext)
    assert isinstance(token, str)

    raw = base64.urlsafe_b64decode(token)
    assert raw[:12]  # nonce present

    decrypted = encryption_service.decrypt(token)
    assert decrypted == plaintext


def test_decrypt_with_modified_token_raises_exception(encryption_service: AesEncryptionService) -> None:
    token = encryption_service.encrypt("hello")
    # Tamper with token by flipping a char
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(AesEncryptionError, match="Failed to decrypt data"):
        encryption_service.decrypt(tampered)


def test_constructor_rejects_non_bytes() -> None:
    with pytest.raises(AesEncryptionError, match="AES key must be bytes"):
        AesEncryptionService(key="not-bytes")  # type: ignore[arg-type]


def test_constructor_rejects_short_key() -> None:
    short_key = os.urandom(8)
    with pytest.raises(AesEncryptionError, match="AES key must be at least 128 bits"):
        AesEncryptionService(key=short_key)


def test_encrypt_produces_different_ciphertexts_for_same_plaintext(encryption_service: AesEncryptionService) -> None:
    t1 = encryption_service.encrypt("same-text")
    t2 = encryption_service.encrypt("same-text")
    assert t1 != t2


def test_decrypt_unpadded_base64_token(encryption_service: AesEncryptionService) -> None:
    token = encryption_service.encrypt("abc")

    # remove padding (if any)
    unpadded = token.rstrip("=")
    with pytest.raises(AesEncryptionError, match="Failed to decrypt data"):
        encryption_service.decrypt(unpadded)

    # add padding back for correct decryption
    padded = unpadded + "=" * (-len(unpadded) % 4)

    assert encryption_service.decrypt(padded) == "abc"


def test_from_encoded_key() -> None:
    raw_key = os.urandom(16)
    encoded_key = base64.urlsafe_b64encode(raw_key).decode()

    service = AesEncryptionService.from_encoded_key(encoded_key=encoded_key)
    assert isinstance(service, AesEncryptionService)


@patch("app.services.aes_encryption_service.AESGCM.encrypt")
def test_encrypt_raises_exception(mock_encrypt: MagicMock, encryption_service: AesEncryptionService) -> None:
    mock_encrypt.side_effect = Exception("Mocked encryption failure")
    with pytest.raises(AesEncryptionError, match="Failed to encrypt data"):
        encryption_service.encrypt("test plaintext")
