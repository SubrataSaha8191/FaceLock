"""PySide6 QObject bridge connecting QML frontend to FaceLock Core backend."""

import json
from typing import Any, Dict, List
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from Core.config.settings import SystemSettings
from Core.config.loader import ConfigLoader
from Core.camera.opencv_camera import OpenCVCamera
from Core.detection.yunet_detector import YuNetDetector
from Core.recognition.sface_extractor import SFaceExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine
from Core.liveness.texture_analyzer import TextureAnalyzer
from Dashboard.backend.camera_provider import LiveCameraProvider
from Dashboard.backend.models import UserViewModel, SystemMetricsViewModel


class FaceLockBridge(QObject):
    """Main QObject bridge controller exposed to QML."""

    userListChanged = Signal()
    statusMessageChanged = Signal(str, bool)
    cameraFrameUpdated = Signal()

    def __init__(self, camera_provider: LiveCameraProvider):
        super().__init__()
        self.camera_provider = camera_provider
        self.config_loader = ConfigLoader()
        self.settings: SystemSettings = self.config_loader.load()

        self.storage = EncryptedSQLiteStorage(self.settings.db_path)
        self.camera = OpenCVCamera(self.settings.camera)
        self.detector = YuNetDetector(score_threshold=self.settings.security.detector_score_threshold)
        self.extractor = SFaceExtractor()
        self.liveness = TextureAnalyzer(self.settings.liveness.texture_threshold)

        self.engine = AuthenticationEngine(
            self.settings, self.detector, self.extractor, self.storage, self.liveness
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_camera_timer_tick)

    def _on_camera_timer_tick(self) -> None:
        if self.camera.is_opened():
            ret, frame = self.camera.read_frame()
            if ret and frame is not None:
                self.camera_provider.update_frame_from_cv(frame)
                self.cameraFrameUpdated.emit()

    @Slot(result=list)
    def getUsers(self) -> List[Dict[str, Any]]:
        """Return list of enrolled users for QML view."""
        users = self.storage.get_all_users()
        return [UserViewModel(u[0], u[1]).to_dict() for u in users]

    @Slot(str, str, str, str, result=bool)
    def enrollUser(self, user_id: str, name: str, secret: str, password: str = "") -> bool:
        """Enroll new user template using current camera frame."""
        if not self.camera.is_opened():
            self.camera.open()
        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            self.statusMessageChanged.emit("Camera frame capture failed", False)
            return False
        success = self.engine.enroll_user(user_id, name, secret, frame, password if password else None)
        msg = f"User '{name}' enrolled successfully" if success else "Enrollment failed (No face / error)"
        self.statusMessageChanged.emit(msg, success)
        if success:
            self.userListChanged.emit()
        return success

    @Slot(str, str, result=bool)
    def verifyUser(self, user_id: str, secret: str) -> bool:
        """Verify user identity using current camera frame."""
        if not self.camera.is_opened():
            self.camera.open()
        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            self.statusMessageChanged.emit("Camera frame capture failed", False)
            return False
        passed, score = self.engine.authenticate_user(user_id, secret, frame)
        msg = f"Auth PASSED (Score: {score:.2f})" if passed else f"Auth FAILED (Score: {score:.2f})"
        self.statusMessageChanged.emit(msg, passed)
        return passed

    @Slot(str, result=bool)
    def deleteUser(self, user_id: str) -> bool:
        """Delete user template from storage."""
        ok = self.storage.delete_user(user_id)
        if ok:
            self.statusMessageChanged.emit(f"User '{user_id}' deleted", True)
            self.userListChanged.emit()
        return ok

    @Slot(result=dict)
    def getMetrics(self) -> Dict[str, Any]:
        """Return system metrics summary."""
        users_count = len(self.storage.get_all_users())
        metrics = SystemMetricsViewModel(
            registered_users_count=users_count,
            camera_active=self.camera.is_opened(),
            liveness_enabled=self.settings.security.liveness_required,
            matching_threshold=self.settings.security.matching_threshold,
        )
        return metrics.to_dict()

    @Slot(bool, result=bool)
    def toggleCamera(self, enable: bool) -> bool:
        """Start or stop live camera stream timer."""
        if enable:
            ok = self.camera.open()
            if ok and not self.timer.isActive():
                self.timer.start(33)  # ~30 FPS
            return ok
        else:
            self.timer.stop()
            self.camera.release()
            return True
