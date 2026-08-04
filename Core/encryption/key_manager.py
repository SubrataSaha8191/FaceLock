"""Key manager for retrieving and managing encryption keys."""

from typing import Optional
from Core.utils.crypto_utils import derive_key, generate_salt


class KeyManager:
    """Manages master encryption key derivation and salt management."""

    def __init__(self, master_secret: str, salt: Optional[bytes] = None):
        if salt is None:
            salt = generate_salt()
        self.salt = salt
        self.master_key = derive_key(master_secret, self.salt)

    def get_key(self) -> bytes:
        """Return the 32-byte derived symmetric key."""
        return self.master_key

    def get_salt(self) -> bytes:
        """Return the salt used for key derivation."""
        return self.salt
