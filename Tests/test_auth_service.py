"""Unit tests for FaceLock Background Authentication Service & Biometric OS Gate."""

import json
import os
import socket
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
from Core.config.settings import SystemSettings
from Service.auth.auth_service import AuthService
from Service.auth.service_client import ServiceClient

TEST_SOCKET = "/tmp/facelock_test.sock" if os.name != "nt" else "tcp://127.0.0.1:0"
UNREACHABLE = "/tmp/facelock_nonexistent.sock" if os.name != "nt" else "tcp://127.0.0.1:1"


def _start_service_thread(tmp_path: Path):
    """Start auth service in a background thread with isolated test settings."""
    settings = SystemSettings(data_dir=tmp_path)
    service = AuthService(socket_path=TEST_SOCKET, settings=settings)
    thread = threading.Thread(target=service.start, daemon=True)
    thread.start()
    for _ in range(50):  # wait until bound (TCP learns its port at bind time)
        if service._server is not None:
            break
        time.sleep(0.05)
    return service


def _client(service, timeout=5.0):
    return ServiceClient(service.address, timeout=timeout, token=service.token)


def test_service_start_and_stop(tmp_path):
    service = _start_service_thread(tmp_path)
    if os.name == "nt":
        assert service.address.startswith("tcp://127.0.0.1:") and service.token
    else:
        assert os.path.exists(TEST_SOCKET)
    service.stop()


def test_service_unknown_action(tmp_path):
    service = _start_service_thread(tmp_path)
    try:
        client = _client(service)
        resp = client.send_request({"action": "unknown_action", "user_id": "test"})
        assert resp["result"] is False
        assert "Unknown action" in resp["message"]
    finally:
        service.stop()


def test_service_check_enrolled_unknown_user(tmp_path):
    service = _start_service_thread(tmp_path)
    try:
        client = _client(service)
        result = client.check_enrolled("nonexistent_user_xyz")
        assert result is False
    finally:
        service.stop()


def test_service_verify_password_unknown_user(tmp_path):
    service = _start_service_thread(tmp_path)
    try:
        client = _client(service)
        result = client.verify_password("nonexistent_user", "password")
        assert result is False
    finally:
        service.stop()


def test_service_client_connection_refused():
    client = ServiceClient(UNREACHABLE, timeout=1.0)
    try:
        client.send_request({"action": "test"})
        assert False, "Should have raised"
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        pass


def test_service_authenticate_face(tmp_path):
    service = _start_service_thread(tmp_path)
    try:
        client = _client(service)
        with patch("cv2.VideoCapture") as mock_cap:
            mock_inst = MagicMock()
            mock_inst.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
            mock_cap.return_value = mock_inst
            result = client.authenticate_face("user_01", "MasterKey123")
            assert isinstance(result, bool)
    finally:
        service.stop()
