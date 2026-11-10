"""The Windows Credential Provider bridge (runs on any OS; it only needs the local service)."""

import importlib.util
import os
import threading
import time
from pathlib import Path

import pytest

from Core.authentication.password_fallback import PasswordFallback
from Core.config.settings import SystemSettings
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Service.auth.auth_service import AuthService

BRIDGE = Path(__file__).resolve().parent.parent / "Windows" / "credential_provider" / "credential_bridge.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("credential_bridge", BRIDGE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def service(monkeypatch):
    data_dir = Path(os.environ["FACELOCK_DATA_DIR"])      # per-test temp dir from conftest
    st = SystemSettings(data_dir=data_dir)
    storage = EncryptedSQLiteStorage(st.db_path)
    storage.save_user("ada", "Ada", b"x", b"s")
    storage.save_user("bob", "Bob", b"x", b"s")   # two profiles: no single-user fallback for unknown names
    storage.save_password_hash("ada", PasswordFallback(st.security.password_hash_iterations).hash_password("open-sesame"))
    svc = AuthService(socket_path="tcp://127.0.0.1:0", settings=st)
    threading.Thread(target=svc.start, daemon=True).start()
    for _ in range(100):
        if svc._server is not None:
            break
        time.sleep(0.05)
    monkeypatch.setenv("FACELOCK_SOCKET", svc.address)    # token is found via endpoint.json in the data dir
    yield svc
    svc.stop()


def test_password_mode_over_the_authenticated_transport(service):
    bridge = _load_bridge()
    assert bridge.verify_windows_user("ada", "open-sesame") is True
    assert bridge.verify_windows_user("ada", "wrong") is False
    assert bridge.main(["bridge", "ada", "open-sesame"]) == bridge.EXIT_OK          # legacy form
    assert bridge.main(["bridge", "ada", "nope"]) == bridge.EXIT_DENIED


def test_password_from_stdin(service, monkeypatch):
    import io
    bridge = _load_bridge()
    monkeypatch.setattr("sys.stdin", io.StringIO("open-sesame\n"))
    assert bridge.main(["bridge", "--password", "ada"]) == bridge.EXIT_OK


def test_face_mode_reports_not_enrolled_as_denied(service):
    bridge = _load_bridge()
    ok, reason = bridge.verify_windows_face("ghost")
    assert ok is False and reason == "not_enrolled"
    assert bridge.main(["bridge", "--face", "ghost"]) == bridge.EXIT_DENIED


def test_service_down_is_distinct_exit_code(monkeypatch, tmp_path):
    monkeypatch.setenv("FACELOCK_SOCKET", "tcp://127.0.0.1:1")
    bridge = _load_bridge()
    assert bridge.verify_windows_face("ada") == (False, "service_unavailable")
    assert bridge.main(["bridge", "--face", "ada"]) == bridge.EXIT_UNAVAILABLE
    assert bridge.verify_windows_user("ada", "x") is False


def test_usage_when_called_without_arguments(capsys):
    bridge = _load_bridge()
    assert bridge.main(["bridge"]) == bridge.EXIT_DENIED
    assert "--face" in capsys.readouterr().out
