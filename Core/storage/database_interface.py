"""Abstract base interface for template database storage."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class IDatabaseStorage(ABC):
    """Interface defining storage operations for user face templates."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize database schema and tables."""
        pass

    @abstractmethod
    def save_user(self, user_id: str, username: str, encrypted_embedding: bytes, salt: bytes) -> bool:
        """Store new user record with encrypted template."""
        pass

    @abstractmethod
    def get_user_embedding(self, user_id: str) -> Optional[bytes]:
        """Fetch encrypted embedding payload for user."""
        pass

    @abstractmethod
    def get_all_users(self) -> List[Tuple[str, str, bytes, bytes]]:
        """Return all user records: (user_id, username, encrypted_embedding, salt)."""
        pass

    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete user record by ID."""
        pass

    @abstractmethod
    def save_password_hash(self, user_id: str, password_hash: bytes) -> bool:
        """Store password hash for fallback authentication."""
        pass

    @abstractmethod
    def get_password_hash(self, user_id: str) -> Optional[bytes]:
        """Retrieve password hash for user."""
        pass
