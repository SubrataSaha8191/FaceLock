"""Cryptographic utility functions for key derivation and salt generation."""

import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_salt(length: int = 16) -> bytes:
    """Generate cryptographically secure random salt."""
    return os.urandom(length)


def derive_key(secret: str, salt: bytes, iterations: int = 100_000) -> bytes:
    """Derive 256-bit symmetric encryption key using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(secret.encode("utf-8"))
