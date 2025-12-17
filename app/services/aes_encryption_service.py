from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os
import logging

logger = logging.getLogger(__name__)


class AesEncryptionError(Exception):
    pass


class AesEncryptionService:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes):
            raise AesEncryptionError("AES key must be bytes")

        if len(key) not in (16, 24, 32):
            raise AesEncryptionError(
                "AES key must be at least 128 bits (16 bytes); recommended lengths are 16, 24, or 32 bytes"
            )

        self._aesgcm = AESGCM(key)

    @staticmethod
    def from_encoded_key(encoded_key: str) -> "AesEncryptionService":
        key_bytes = base64.urlsafe_b64decode(encoded_key)
        return AesEncryptionService(key=key_bytes)

    def encrypt(self, plaintext: str) -> str:
        try:
            nonce = os.urandom(12)
            ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
            return base64.urlsafe_b64encode(nonce + ciphertext).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise AesEncryptionError("Failed to encrypt data") from e

    def decrypt(self, encrypted_data: str) -> str:
        try:
            raw = base64.urlsafe_b64decode(encrypted_data)
            nonce = raw[:12]
            ciphertext = raw[12:]
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise AesEncryptionError("Failed to decrypt data") from e
