"""UNIX domain socket authentication service for OS-level integrations."""

import json
import os
import socket
import threading
import sys
from pathlib import Path
from typing import Optional

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Core.config.settings import SystemSettings
from Core.config.loader import ConfigLoader
from Core.detection.cascade_detector import CascadeDetector
from Core.recognition.feature_extractor import FeatureExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine
from Core.liveness.texture_analyzer import TextureAnalyzer
from Core.utils.logger import get_logger

logger = get_logger("AuthService")
DEFAULT_SOCKET_PATH = "/tmp/facelock.sock"


class AuthService:
    """Background socket server exposing FaceLock auth to PAM/OS modules."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH, settings: Optional[SystemSettings] = None):
        self.socket_path = socket_path
        self.config_loader = ConfigLoader()
        self.settings: SystemSettings = settings or self.config_loader.load()

        self.storage = EncryptedSQLiteStorage(self.settings.db_path)
        self.detector = CascadeDetector()
        self.extractor = FeatureExtractor()
        self.liveness = TextureAnalyzer(self.settings.liveness.texture_threshold)
        self.engine = AuthenticationEngine(
            self.settings, self.detector, self.extractor, self.storage, self.liveness
        )

        self._server: Optional[socket.socket] = None
        self._running = False

    def start(self) -> None:
        """Start the UNIX socket server."""
        self._cleanup_socket()
        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(self.socket_path)
        try: os.chmod(self.socket_path, 0o666)
        except Exception: pass
        self._server.listen(5)
        self._server.settimeout(1.0)
        self._running = True
        logger.info(f"Auth service listening on {self.socket_path}")

        while self._running:
            try:
                conn, _ = self._server.accept()
                thread = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                thread.start()
            except socket.timeout:
                continue

    def stop(self) -> None:
        """Shutdown the socket server."""
        self._running = False
        if self._server: self._server.close()
        self._cleanup_socket()
        logger.info("Auth service stopped.")

    def _handle_client(self, conn: socket.socket) -> None:
        """Process a single client JSON request."""
        try:
            data = conn.recv(4096).decode("utf-8")
            request = json.loads(data)
            response = self._process_request(request)
            conn.sendall(json.dumps(response).encode("utf-8"))
        except Exception as e:
            error_resp = {"result": False, "message": str(e)}
            conn.sendall(json.dumps(error_resp).encode("utf-8"))
        finally:
            conn.close()

    def _resolve_user(self, user_id: str) -> str:
        enrolled = self.storage.get_all_users()
        if not enrolled: return user_id
        for u in enrolled:
            if user_id in (u[0], u[1], u[1].lower(), u[1].lower().replace(" ", "-"), u[1].lower().replace(" ", "_")):
                return u[0]
        return enrolled[0][0] if len(enrolled) == 1 else user_id

    def _process_request(self, request: dict) -> dict:
        """Route request to appropriate auth method."""
        action = request.get("action", "")
        raw_user_id = request.get("user_id", "")
        user_id = self._resolve_user(raw_user_id)

        if action == "verify_password":
            password = request.get("password", "")
            ok = self.engine.authenticate_with_password(user_id, password)
            msg = "Password verified" if ok else "Password rejected"
            return {"result": ok, "message": msg}

        if action == "authenticate_face":
            secret = request.get("secret", "MasterKey123")
            import cv2, time, numpy as np
            frame = None
            for attempt in range(4):
                cap = cv2.VideoCapture(self.settings.camera.device_id)
                if cap.isOpened():
                    for _ in range(8):
                        ret, f = cap.read()
                        if ret and f is not None: frame = f
                        time.sleep(0.03)
                    cap.release()
                if frame is not None and frame.size > 0 and np.mean(frame) > 10: break
                time.sleep(0.1)
            if frame is None or frame.size == 0 or np.mean(frame) <= 10:
                return {"result": False, "message": "Camera frame capture failed or underexposed"}
            ok, sim = self.engine.authenticate_user(user_id, secret, frame)
            return {"result": ok, "similarity": round(float(sim), 4), "message": "Face match verified" if ok else "Face auth failed"}

        if action == "check_enrolled":
            enrolled = self.storage.get_all_users()
            is_enrolled = len(enrolled) > 0 and (
                user_id in [u[0] for u in enrolled] or
                any(raw_user_id in (u[0], u[1], u[1].lower(), u[1].lower().replace(" ", "-"), u[1].lower().replace(" ", "_")) for u in enrolled) or
                len(enrolled) == 1
            )
            return {"result": is_enrolled, "message": "enrollment_check"}

        return {"result": False, "message": f"Unknown action: {action}"}

    def _cleanup_socket(self) -> None:
        """Remove stale socket file."""
        if os.path.exists(self.socket_path):
            try: os.unlink(self.socket_path)
            except Exception: pass


if __name__ == "__main__":
    service = AuthService()
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()
