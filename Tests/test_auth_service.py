"""Unit tests for FaceLock Background Authentication Service."""

import json
import socket
import threading
import time

from Service.auth.auth_service import AuthService
from Service.auth.service_client import ServiceClient

TEST_SOCKET = "/tmp/facelock_test.sock"


def _start_service_thread():
    """Start auth service in a background thread for testing."""
    service = AuthService(socket_path=TEST_SOCKET)
    thread = threading.Thread(target=service.start, daemon=True)
    thread.start()
    time.sleep(0.3)  # Allow socket to bind
    return service


def test_service_start_and_stop():
    service = _start_service_thread()
    # Verify socket file exists
    import os
    assert os.path.exists(TEST_SOCKET)
    service.stop()


def test_service_unknown_action():
    service = _start_service_thread()
    try:
        client = ServiceClient(TEST_SOCKET, timeout=5.0)
        resp = client.send_request({"action": "unknown_action", "user_id": "test"})
        assert resp["result"] is False
        assert "Unknown action" in resp["message"]
    finally:
        service.stop()


def test_service_check_enrolled_unknown_user():
    service = _start_service_thread()
    try:
        client = ServiceClient(TEST_SOCKET, timeout=5.0)
        result = client.check_enrolled("nonexistent_user_xyz")
        assert result is False
    finally:
        service.stop()


def test_service_verify_password_unknown_user():
    service = _start_service_thread()
    try:
        client = ServiceClient(TEST_SOCKET, timeout=5.0)
        result = client.verify_password("nonexistent_user", "password")
        assert result is False
    finally:
        service.stop()


def test_service_client_connection_refused():
    """Client should raise ConnectionRefusedError when service is not running."""
    client = ServiceClient("/tmp/facelock_nonexistent.sock", timeout=1.0)
    try:
        client.send_request({"action": "test"})
        assert False, "Should have raised"
    except (ConnectionRefusedError, FileNotFoundError):
        pass
