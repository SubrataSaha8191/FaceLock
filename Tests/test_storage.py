"""Unit tests for encrypted SQLite storage."""

from pathlib import Path
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage


def test_sqlite_storage(tmp_path: Path):
    db_file = tmp_path / "test_facelock.db"
    storage = EncryptedSQLiteStorage(db_file)

    user_id = "user001"
    username = "Alice"
    dummy_payload = b"encrypted_vector_data"
    dummy_salt = b"random_salt_1234"

    # Save
    saved = storage.save_user(user_id, username, dummy_payload, dummy_salt)
    assert saved is True

    # Retrieve
    fetched_payload = storage.get_user_embedding(user_id)
    assert fetched_payload == dummy_payload

    # All users
    all_users = storage.get_all_users()
    assert len(all_users) == 1
    assert all_users[0][0] == user_id
    assert all_users[0][1] == username

    # Delete
    deleted = storage.delete_user(user_id)
    assert deleted is True
    assert storage.get_user_embedding(user_id) is None
