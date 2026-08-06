"""SQLite implementation of encrypted template database."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

from Core.storage.database_interface import IDatabaseStorage


class EncryptedSQLiteStorage(IDatabaseStorage):
    """SQLite implementation storing encrypted face vectors and password hashes."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def initialize(self) -> None:
        """Create users and password_hashes tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    encrypted_embedding BLOB NOT NULL,
                    salt BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_hashes (
                    user_id TEXT PRIMARY KEY,
                    password_hash BLOB NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()

    def save_user(self, user_id: str, username: str, encrypted_embedding: bytes, salt: bytes) -> bool:
        """Insert or replace a user template."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users (user_id, username, encrypted_embedding, salt)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, encrypted_embedding, salt))
                conn.commit()
            return True
        except Exception:
            return False

    def get_user_embedding(self, user_id: str) -> Optional[bytes]:
        """Fetch encrypted vector BLOB for a specific user ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_embedding FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all_users(self) -> List[Tuple[str, str, bytes, bytes]]:
        """Return list of all registered users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, encrypted_embedding, salt FROM users")
            return cursor.fetchall()

    def delete_user(self, user_id: str) -> bool:
        """Delete user template from database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM password_hashes WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_username(self, user_id: str, new_username: str) -> bool:
        """Update enrolled user's username in database."""
        return self.update_identity(user_id, user_id, new_username)

    def update_identity(self, old_user_id: str, new_user_id: str, new_username: str) -> bool:
        """Update enrolled user's ID and username in database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if old_user_id != new_user_id:
                    cursor.execute("UPDATE password_hashes SET user_id = ? WHERE user_id = ?", (new_user_id, old_user_id))
                    cursor.execute("UPDATE users SET user_id = ?, username = ? WHERE user_id = ?", (new_user_id, new_username, old_user_id))
                else:
                    cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (new_username, old_user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False

    def save_password_hash(self, user_id: str, password_hash: bytes) -> bool:
        """Store or update password hash for fallback authentication."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO password_hashes (user_id, password_hash)
                    VALUES (?, ?)
                """, (user_id, password_hash))
                conn.commit()
            return True
        except Exception:
            return False

    def get_password_hash(self, user_id: str) -> Optional[bytes]:
        """Retrieve stored password hash for user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM password_hashes WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None
