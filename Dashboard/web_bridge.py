"""PyWebView API bridge — exposes FaceLock backend to the JS frontend."""

import base64
import json
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Any, Dict, List

from Core.config.settings import SystemSettings
from Core.config.loader import ConfigLoader
from Core.camera.opencv_camera import OpenCVCamera
from Core.detection.cascade_detector import CascadeDetector
from Core.recognition.feature_extractor import FeatureExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine
from Core.liveness.texture_analyzer import TextureAnalyzer


class FaceLockWebBridge:
    """API object exposed to pywebview JS frontend via `window.pywebview.api`."""

    def __init__(self):
        self.config_loader = ConfigLoader()
        self.settings: SystemSettings = self.config_loader.load()

        self.storage = EncryptedSQLiteStorage(self.settings.db_path)
        self.camera = OpenCVCamera(self.settings.camera)
        self.detector = CascadeDetector()
        self.extractor = FeatureExtractor()
        self.liveness = TextureAnalyzer(self.settings.liveness.texture_threshold)

        self.engine = AuthenticationEngine(
            self.settings, self.detector, self.extractor,
            self.storage, self.liveness,
        )
        self._camera_active = False

    def get_users(self) -> List[Dict[str, Any]]:
        """Return enrolled user list."""
        users = self.storage.get_all_users()
        return [{"userId": u[0], "username": u[1]} for u in users]

    def get_metrics(self) -> Dict[str, Any]:
        """Return system metrics summary."""
        users_count = len(self.storage.get_all_users())
        socket_path = self.settings.data_dir / "facelock.sock"
        return {
            "registeredUsersCount": users_count,
            "cameraActive": self._camera_active,
            "livenessEnabled": self.settings.security.liveness_required,
            "matchingThreshold": self.settings.security.matching_threshold,
            "daemonActive": True,
            "socketPath": str(socket_path),
        }

    def save_settings(self, matching_threshold: float, liveness_enabled: bool) -> Dict[str, Any]:
        """Dynamically update and persist system security settings."""
        self.settings.security.matching_threshold = float(matching_threshold)
        self.settings.security.liveness_required = bool(liveness_enabled)
        self.config_loader.save(self.settings)
        return {"ok": True, "msg": "Settings persisted successfully"}

    def get_logs(self) -> List[Dict[str, Any]]:
        """Dynamically read audit log file records."""
        log_file = Path(self.settings.audit_log_path)
        if not log_file.exists():
            return []
        records = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        records.append({
                            "event": data.get("event", "UNKNOWN"),
                            "user": data.get("user_id", "system"),
                            "status": "OK" if data.get("success", True) else "FAIL",
                            "ts": data.get("timestamp", "").split("T")[-1][:8] if "timestamp" in data else "--:--:--"
                        })
        except Exception:
            pass
        return records[-20:]  # Latest 20 records

    def enroll_user(self, user_id: str, name: str, secret: str) -> Dict:
        """Enroll new identity using current camera frame."""
        if not self.camera.is_opened():
            self.camera.open()
        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            return {"ok": False, "msg": "Camera capture failed"}
        ok = self.engine.enroll_user(user_id, name, secret, frame, None)
        msg = f"'{name}' enrolled" if ok else "Enrollment failed"
        return {"ok": ok, "msg": msg}

    def delete_user(self, user_id: str) -> Dict:
        """Remove identity from encrypted store."""
        ok = self.storage.delete_user(user_id)
        return {"ok": ok, "msg": f"'{user_id}' deleted" if ok else "Delete failed"}

    def update_user(self, old_user_id: str, new_user_id: str, new_name: str) -> Dict:
        """Update identity details (User ID and Full Name) in encrypted database."""
        ok = self.storage.update_identity(old_user_id, new_user_id, new_name)
        return {"ok": ok, "msg": f"Identity '{new_name}' updated successfully" if ok else "Update failed"}

    def toggle_camera(self, enable: bool) -> Dict:
        """Start or stop camera stream."""
        if enable:
            ok = self.camera.open()
            self._camera_active = ok
            return {"ok": ok}
        self.camera.release()
        self._camera_active = False
        return {"ok": True}

    def get_camera_frame(self) -> str:
        """Capture one frame and return base64 JPEG data URI."""
        if not self.camera.is_opened():
            return ""
        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            return ""
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        b64 = base64.b64encode(buf).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
