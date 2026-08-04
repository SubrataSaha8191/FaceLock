"""Storage package for biometric templates."""

from Core.storage.database_interface import IDatabaseStorage
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage

__all__ = ["IDatabaseStorage", "EncryptedSQLiteStorage"]
