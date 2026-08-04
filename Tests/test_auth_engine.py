"""Unit tests for enhanced authentication engine with Phase 2 features."""

from pathlib import Path
import numpy as np

from Core.config.settings import SystemSettings
from Core.detection.detector_interface import IFaceDetector
from Core.liveness.liveness_interface import ILivenessDetector
from Core.liveness.liveness_result import LivenessResult
from Core.recognition.feature_extractor import FeatureExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine


class MockDetector(IFaceDetector):
    """Mock detector returning fixed bounding box."""
    def detect_faces(self, frame):
        return [(10, 10, 100, 100)]


class MockLivenessPass(ILivenessDetector):
    """Mock liveness that always passes."""
    def check_liveness(self, frame, bbox):
        return LivenessResult(is_live=True, confidence=0.95, method="mock")


class MockLivenessFail(ILivenessDetector):
    """Mock liveness that always fails."""
    def check_liveness(self, frame, bbox):
        return LivenessResult(is_live=False, confidence=0.1, method="mock")


def _create_engine(tmp_path, liveness=None):
    settings = SystemSettings(data_dir=tmp_path, db_name="test.db")
    storage = EncryptedSQLiteStorage(settings.db_path)
    return AuthenticationEngine(
        settings, MockDetector(), FeatureExtractor(), storage, liveness
    )


def test_enroll_and_auth_with_liveness(tmp_path: Path):
    engine = _create_engine(tmp_path, MockLivenessPass())
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 150
    assert engine.enroll_user("u1", "Alice", "secret", frame) is True
    passed, score = engine.authenticate_user("u1", "secret", frame)
    assert passed is True
    assert score >= 0.6


def test_liveness_failure_blocks_auth(tmp_path: Path):
    engine = _create_engine(tmp_path, MockLivenessFail())
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 150
    engine.enroll_user("u2", "Bob", "secret", frame)
    passed, _ = engine.authenticate_user("u2", "secret", frame)
    assert passed is False


def test_lockout_after_max_failures(tmp_path: Path):
    engine = _create_engine(tmp_path, MockLivenessFail())
    settings = engine.settings
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 150
    engine.enroll_user("u3", "Carol", "secret", frame)

    for _ in range(settings.security.max_auth_attempts):
        engine.authenticate_user("u3", "secret", frame)

    assert engine.tracker.is_locked("u3") is True


def test_password_fallback(tmp_path: Path):
    engine = _create_engine(tmp_path)
    frame = np.ones((200, 200, 3), dtype=np.uint8) * 150
    engine.enroll_user("u4", "Dave", "secret", frame, password="Str0ngPw!")

    assert engine.authenticate_with_password("u4", "Str0ngPw!") is True
    assert engine.authenticate_with_password("u4", "WrongPw1") is False
    assert engine.authenticate_with_password("unknown", "any") is False
