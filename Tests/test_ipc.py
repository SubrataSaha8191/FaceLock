"""Local IPC: authenticated loopback TCP (used on Windows) and owner-only file helper."""

import json
import os
import socket
import threading
import time
from pathlib import Path

import pytest

from Core.config.settings import SystemSettings, get_default_data_dir
from Core.utils import ipc
from Core.utils.fs_security import restrict_to_owner
from Service.auth.auth_service import AuthService
from Service.auth.service_client import ServiceClient


def _start(tmp_path):
    svc = AuthService(socket_path="tcp://127.0.0.1:0", settings=SystemSettings(data_dir=tmp_path))
    threading.Thread(target=svc.start, daemon=True).start()
    for _ in range(100):
        if svc._server is not None:
            break
        time.sleep(0.05)
    return svc


def test_tcp_service_publishes_endpoint_and_loopback_only(tmp_path):
    svc = _start(tmp_path)
    try:
        ep = json.loads((tmp_path / "endpoint.json").read_text())
        assert ep["host"] == "127.0.0.1" and ep["port"] > 0 and len(ep["token"]) >= 32
        assert svc._server.getsockname()[0] == "127.0.0.1"
        assert svc.address == f"tcp://127.0.0.1:{ep['port']}"
    finally:
        svc.stop()
    assert not (tmp_path / "endpoint.json").exists()  # removed on stop


def test_requests_without_the_token_are_rejected(tmp_path):
    svc = _start(tmp_path)
    try:
        assert ServiceClient(svc.address, 5, token=svc.token).send_request({"action": "ping"})["result"] is True
        bad = ServiceClient(svc.address, 5, token="wrong").send_request({"action": "ping"})
        assert bad["result"] is False and bad["reason"] == "unauthorized"
        # With the endpoint file removed and no token given there is nothing to authenticate with.
        (tmp_path / "endpoint.json").unlink()
        none = ServiceClient(svc.address, 5).send_request({"action": "ping"})
        assert none["reason"] == "unauthorized"
    finally:
        svc.stop()


def test_auto_address_resolves_through_endpoint_file(tmp_path, monkeypatch):
    svc = _start(tmp_path)
    try:
        monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path))
        resp = ServiceClient("auto", 5).send_request({"action": "ping"})
        assert resp["result"] is True
        assert ipc.probe("auto") is True
    finally:
        svc.stop()
    assert ipc.probe("auto") is False  # endpoint gone: not running


def test_auto_without_a_service_is_a_clean_connection_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FACELOCK_DATA_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        ServiceClient("auto", 1).send_request({"action": "ping"})


def test_refuses_to_listen_off_loopback(tmp_path):
    with pytest.raises(ValueError):
        ipc.bind_server("tcp://0.0.0.0:0", tmp_path)


def test_token_comparison():
    assert ipc.token_ok(None, None) is True          # unix sockets: no token required
    assert ipc.token_ok("abc", "abc") is True
    assert ipc.token_ok("abc", "abd") is False and ipc.token_ok("abc", None) is False and ipc.token_ok("abc", 5) is False


def test_default_address_and_data_dir_per_platform(monkeypatch):
    monkeypatch.delenv("FACELOCK_SOCKET", raising=False)
    assert ipc.default_address() == ("auto" if os.name == "nt" else "/tmp/facelock.sock")
    monkeypatch.setenv("FACELOCK_SOCKET", "tcp://127.0.0.1:9")
    assert ipc.default_address() == "tcp://127.0.0.1:9"
    monkeypatch.delenv("FACELOCK_DATA_DIR", raising=False)
    d = str(get_default_data_dir())
    assert d.endswith("FaceLock") if os.name == "nt" else d.endswith(".facelock")


def test_get_default_data_dir_never_needs_posix_only_calls(monkeypatch):
    """Regression: a first start on Windows used to crash on os.geteuid()."""
    monkeypatch.delenv("FACELOCK_DATA_DIR", raising=False)
    if hasattr(os, "geteuid"):
        monkeypatch.delattr(os, "geteuid")
    assert get_default_data_dir()  # must not raise


def test_restrict_to_owner(tmp_path: Path):
    f = tmp_path / "secret.json"
    f.write_text("{}")
    ok = restrict_to_owner(f)
    assert isinstance(ok, bool)
    if os.name != "nt":
        assert ok and (os.stat(f).st_mode & 0o077) == 0
    assert restrict_to_owner(tmp_path / "missing.json") is False
