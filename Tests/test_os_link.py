"""Face profile <-> OS account link, used by the lock screen, sudo and the app gate."""

from pathlib import Path

from Core.config.settings import SystemSettings
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Service.auth.auth_service import AuthService


def test_link_survives_rescan_and_template_updates(tmp_path: Path):
    s = EncryptedSQLiteStorage(tmp_path / "t.db")
    s.save_user("ada", "Ada", b"v1", b"salt")
    assert s.set_os_user("ada", "ada-pc")
    # A re-scan or an adaptive update re-saves the row; the link must stay.
    s.save_user("ada", "Ada", b"v2", b"salt", template_format=2)
    assert s.find_user_by_os_account("ada-pc") == "ada"
    assert s.get_user_embedding("ada") == b"v2"


def test_link_lookup_and_unlink(tmp_path: Path):
    s = EncryptedSQLiteStorage(tmp_path / "t.db")
    s.save_user("a", "A", b"x", b"s"); s.save_user("b", "B", b"x", b"s")
    s.set_os_user("b", "bob")
    assert s.find_user_by_os_account("bob") == "b" and s.os_account_taken("bob")
    assert s.find_user_by_os_account("nobody") is None and s.find_user_by_os_account("") is None
    s.set_os_user("b", None)
    assert not s.os_account_taken("bob")


def test_link_follows_a_renamed_profile(tmp_path: Path):
    s = EncryptedSQLiteStorage(tmp_path / "t.db")
    s.save_user("a", "A", b"x", b"s"); s.set_os_user("a", "alice")
    s.update_identity("a", "a2", "Alice")
    assert s.find_user_by_os_account("alice") == "a2"


def _service(tmp_path):
    return AuthService(socket_path=str(tmp_path / "s.sock"), settings=SystemSettings(data_dir=tmp_path))


def test_service_resolves_os_account_even_with_several_profiles(tmp_path: Path):
    svc = _service(tmp_path)
    for uid, name in (("one", "Person One"), ("two", "Person Two")):
        svc.storage.save_user(uid, name, b"x", b"s")
    svc.storage.set_os_user("two", "login-name")
    assert svc._resolve_user("login-name") == "two"      # explicit link wins
    assert svc._resolve_user("person-one") == "one"      # name match still works
    assert svc._process_request({"action": "check_enrolled", "user_id": "login-name"})["result"] is True


def test_service_ping_reports_version_and_readiness(tmp_path: Path):
    r = _service(tmp_path)._process_request({"action": "ping"})
    assert r["result"] is True and r["version"] and r["ready"] is True
