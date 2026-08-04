"""Password fallback authentication using PBKDF2 hashing."""

import hashlib
import os
from typing import Optional


class PasswordFallback:
    """Provides secure password hashing and verification as a fallback.

    Used when face authentication fails after max attempts or
    when liveness detection fails.
    """

    def __init__(self, iterations: int = 100_000):
        self.iterations = iterations

    def hash_password(self, password: str) -> bytes:
        """Generate salted PBKDF2-HMAC-SHA256 hash of password."""
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.iterations
        )
        # Store as salt + key (16 + 32 = 48 bytes)
        return salt + key

    def verify_password(self, password: str, stored_hash: bytes) -> bool:
        """Verify password against stored salted hash."""
        if len(stored_hash) < 48:
            return False
        salt = stored_hash[:16]
        expected_key = stored_hash[16:]
        actual_key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.iterations
        )
        return actual_key == expected_key

    @staticmethod
    def is_strong_password(password: str) -> bool:
        """Basic password strength check."""
        if len(password) < 8:
            return False
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        return has_upper and has_lower and has_digit
