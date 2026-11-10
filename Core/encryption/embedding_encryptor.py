"""AES-GCM encryptor for face embedding vectors."""

import os
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EmbeddingEncryptor:
    """Encrypts and decrypts NumPy embedding vectors using AES-GCM."""

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("AES-GCM key must be 32 bytes (256 bits).")
        self.aesgcm = AESGCM(key)

    def encrypt_vector(self, embedding: np.ndarray) -> bytes:
        """Serialize and encrypt a floating point embedding array."""
        nonce = os.urandom(12)
        raw_bytes = embedding.astype(np.float32).tobytes()
        ciphertext = self.aesgcm.encrypt(nonce, raw_bytes, None)
        # Store nonce + ciphertext combined
        return nonce + ciphertext

    def encrypt_bytes(self, payload: bytes) -> bytes:
        """Encrypt an arbitrary payload (nonce + ciphertext)."""
        nonce = os.urandom(12)
        return nonce + self.aesgcm.encrypt(nonce, payload, None)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt a payload produced by :meth:`encrypt_bytes`."""
        if len(encrypted_data) < 13:
            raise ValueError("Invalid ciphertext length.")
        return self.aesgcm.decrypt(encrypted_data[:12], encrypted_data[12:], None)

    def decrypt_vector(self, encrypted_data: bytes, vector_dim: int = 128) -> np.ndarray:
        """Decrypt payload back into NumPy floating point array."""
        if len(encrypted_data) < 13:
            raise ValueError("Invalid ciphertext length.")
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        raw_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
        return np.frombuffer(raw_bytes, dtype=np.float32)
