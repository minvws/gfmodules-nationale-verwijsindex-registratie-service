import os
import base64
import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.aes_encryption_service import AesEncryptionService, AesEncryptionError


def test_encrypt_decrypt():
    key = AESGCM.generate_key(bit_length=128)
    service = AesEncryptionService(key=key)

    plaintext = "patient-12345"
    token = service.encrypt(plaintext)
    assert isinstance(token, str)

    # token should be urlsafe base64 decodable
    padded = token + "=" * (-len(token) % 4)
    raw = base64.urlsafe_b64decode(padded)
    assert raw[:12]  # nonce present

    decrypted = service.decrypt(token)
    assert decrypted == plaintext


def test_decrypt_with_modified_token_raises():
    key = AESGCM.generate_key(bit_length=128)
    service = AesEncryptionService(key=key)

    token = service.encrypt("hello")
    # Tamper with token by flipping a char
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(AesEncryptionError):
        service.decrypt(tampered)


def test_constructor_rejects_non_bytes():
    with pytest.raises(AesEncryptionError):
        AesEncryptionService(key="not-bytes")  # type: ignore[arg-type]


def test_constructor_rejects_short_key():
    short_key = os.urandom(8)  # 64-bit
    with pytest.raises(AesEncryptionError):
        AesEncryptionService(key=short_key)


def test_encrypt_produces_different_ciphertexts_for_same_plaintext():
    key = AESGCM.generate_key(bit_length=128)
    service = AesEncryptionService(key=key)

    t1 = service.encrypt("same-text")
    t2 = service.encrypt("same-text")
    assert t1 != t2


def test_decrypt_handles_unpadded_base64_token():
    key = AESGCM.generate_key(bit_length=128)
    service = AesEncryptionService(key=key)
    token = service.encrypt("abc")

    # remove padding (if any) and ensure decrypt still works
    unpadded = token.rstrip("=")
    assert service.decrypt(unpadded) == "abc"

