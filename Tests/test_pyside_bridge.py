"""Unit tests for PySide6 QML Bridge and LiveCameraProvider."""

import os
import numpy as np
import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QImage

from Dashboard.backend.camera_provider import LiveCameraProvider
from Dashboard.backend.bridge import FaceLockBridge


@pytest.fixture(scope="module")
def qapp():
    """Ensure a QGuiApplication exists for Qt object testing in offscreen mode."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])
    return app


def test_live_camera_provider_placeholder(qapp):
    provider = LiveCameraProvider()
    img = provider.requestImage("frame", QSize(), QSize())
    assert isinstance(img, QImage)
    assert not img.isNull()
    assert img.width() == 640
    assert img.height() == 480


def test_live_camera_provider_frame_update(qapp):
    provider = LiveCameraProvider()
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    provider.update_frame_from_cv(fake_frame)
    img = provider.requestImage("frame", QSize(), QSize())
    assert img.width() == 100
    assert img.height() == 100


def test_facelock_bridge_metrics_and_users(qapp):
    provider = LiveCameraProvider()
    bridge = FaceLockBridge(provider)

    users = bridge.getUsers()
    assert isinstance(users, list)

    metrics = bridge.getMetrics()
    assert "registeredUsersCount" in metrics
    assert "cameraActive" in metrics
    assert "livenessEnabled" in metrics
    assert "matchingThreshold" in metrics


def test_facelock_bridge_camera_toggle(qapp):
    provider = LiveCameraProvider()
    bridge = FaceLockBridge(provider)

    # Toggle camera off
    ok = bridge.toggleCamera(False)
    assert ok is True
    assert bridge.getMetrics()["cameraActive"] is False
