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
from Core.camera.stream import CameraStream
from Core.detection.yunet_detector import YuNetDetector
from Core.models import ModelUnavailableError
from Core.recognition.sface_extractor import SFaceExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine
from Core.liveness.texture_analyzer import TextureAnalyzer
from Core.utils import ipc
from Core.utils.logger import get_logger

logger = get_logger("AuthService")
DEFAULT_SOCKET_PATH = ipc.default_address()  # /tmp/facelock.sock on POSIX, "auto" (loopback TCP + token) on Windows
SERVICE_VERSION = "2.0"


class AuthService:
    """Background socket server exposing FaceLock auth to PAM/OS modules."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH, settings: Optional[SystemSettings] = None):
        self.socket_path = socket_path
        self.address = socket_path      # resolved after start() (TCP picks its port then)
        self.token = None               # per-run secret on TCP transports
        self.config_loader = ConfigLoader()
        self.settings: SystemSettings = settings or self.config_loader.load()

        self.storage = EncryptedSQLiteStorage(self.settings.db_path)
        self.liveness = TextureAnalyzer(self.settings.liveness.texture_threshold)
        self.engine: Optional[AuthenticationEngine] = None
        self._init_error: Optional[str] = None
        try:
            self.detector = YuNetDetector(
                score_threshold=self.settings.security.detector_score_threshold
            )
            self.extractor = SFaceExtractor()
            self.engine = AuthenticationEngine(
                self.settings, self.detector, self.extractor, self.storage, self.liveness
            )
        except ModelUnavailableError as exc:
            self._init_error = str(exc)
            logger.error(f"Face models unavailable: {exc}")
        # One unlock at a time: the camera is a single shared device.
        self._camera_lock = threading.Lock()
        self._config_mtime = self._config_stamp()

        self._server: Optional[socket.socket] = None
        self._running = False

    def start(self) -> None:
        """Start the local socket server (UNIX socket on POSIX, authenticated loopback TCP on Windows)."""
        self._server, self.address, self.token = ipc.bind_server(self.socket_path, self.settings.data_dir)
        self._server.settimeout(1.0)
        self._running = True
        logger.info(f"Auth service listening on {self.address}")

        while self._running:
            try:
                conn, _ = self._server.accept()
                thread = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                thread.start()
            except socket.timeout:
                continue
            except OSError:
                break  # server socket closed by stop()

    def stop(self) -> None:
        """Shutdown the socket server."""
        self._running = False
        if self._server: self._server.close()
        self._cleanup_socket()
        logger.info("Auth service stopped.")

    def _handle_client(self, conn: socket.socket) -> None:
        """Process a single client JSON request."""
        try:
            data = conn.recv(65536).decode("utf-8")
            if not data.strip():
                return  # availability probe: client connected and hung up
            try:
                request = json.loads(data)
                if not ipc.token_ok(self.token, request.get("token")):
                    response = {"result": False, "reason": "unauthorized", "message": "Unauthorized"}
                    conn.sendall(json.dumps(response).encode("utf-8"))
                    return
                response = self._process_request(request)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                response = {"result": False, "message": str(e)}
            try:
                conn.sendall(json.dumps(response).encode("utf-8"))
            except OSError:
                pass  # client gave up waiting (e.g. its own timeout)
        finally:
            conn.close()

    def _resolve_user(self, user_id: str) -> str:
        # An explicit link (made at enrollment) between the OS account and a face profile wins.
        linked = self.storage.find_user_by_os_account(user_id)
        if linked:
            return linked
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

        if action == "ping":
            return {"result": True, "version": SERVICE_VERSION, "pipeline": "yunet+sface",
                    "ready": self.engine is not None, "message": "pong"}

        if action == "verify_password":
            password = request.get("password", "")
            ok = self.engine.authenticate_with_password(user_id, password)
            msg = "Password verified" if ok else "Password rejected"
            return {"result": ok, "message": msg}

        if action == "authenticate_face":
            return self._authenticate_face(user_id, request.get("secret", "MasterKey123"))

        if action == "check_enrolled":
            enrolled = self.storage.get_all_users()
            usable = [u for u in enrolled if (self.storage.get_template_format(u[0]) or 0) >= 2]
            if enrolled and not usable:
                # Only old-format profiles exist: report "not enrolled" so PAM falls
                # back to the password instead of failing face unlock repeatedly.
                return {"result": False, "message": "re_enroll_required", "reason": "re_enroll_required"}
            enrolled = usable
            is_enrolled = len(enrolled) > 0 and (
                user_id in [u[0] for u in enrolled] or
                any(raw_user_id in (u[0], u[1], u[1].lower(), u[1].lower().replace(" ", "-"), u[1].lower().replace(" ", "_")) for u in enrolled) or
                len(enrolled) == 1
            )
            return {"result": is_enrolled, "message": "enrollment_check"}

        return {"result": False, "message": f"Unknown action: {action}"}

    def _config_stamp(self) -> float:
        try:
            return self.config_loader.config_path.stat().st_mtime
        except OSError:
            return 0.0

    def _refresh_settings(self) -> None:
        """Pick up dashboard changes (sensitivity, timeout...) without a restart."""
        stamp = self._config_stamp()
        if stamp == self._config_mtime or self.engine is None:
            return
        self._config_mtime = stamp
        try:
            self.settings = self.config_loader.load()
            self.engine.apply_settings(self.settings)
            self.detector._score = self.settings.security.detector_score_threshold
            logger.info("Settings reloaded.")
        except Exception as exc:
            logger.warning(f"Settings reload failed: {exc}")

    def _authenticate_face(self, user_id: str, secret: str) -> dict:
        """Run one streaming unlock attempt against the camera."""
        if self.engine is None:
            return {"result": False, "reason": "models_unavailable",
                    "message": self._init_error or "Face models are not installed"}
        self._refresh_settings()

        # Answer enrollment problems before touching the camera.
        if not any(u[0] == user_id for u in self.storage.get_all_users()):
            return {"result": False, "reason": "not_enrolled",
                    "message": "No face profile enrolled for this user"}
        fmt = self.storage.get_template_format(user_id) or 0
        if fmt < 2:
            return {"result": False, "reason": "re_enroll_required",
                    "message": "Face profile is from an older version. Please enroll again"}

        timeout = self.settings.security.auth_timeout_seconds
        with self._camera_lock:
            stream = CameraStream(self.settings.camera)
            if not stream.open():
                return {"result": False, "reason": "camera_unavailable",
                        "message": "Camera unavailable"}
            try:
                res = self.engine.authenticate_frames(
                    user_id, secret, stream.frames(timeout), timeout=timeout
                )
            finally:
                stream.close()

        logger.info(
            f"Unlock '{user_id}': {res.reason} score={res.score:.3f} "
            f"threshold={res.threshold:.2f} frames={res.frames}"
        )
        return {
            "result": res.ok,
            "similarity": round(float(res.score), 4),
            "reason": res.reason,
            "message": res.message,
            "frames": res.frames,
            "threshold": round(float(res.threshold), 3),
        }

    def _cleanup_socket(self) -> None:
        """Remove the stale socket file (POSIX) or the published endpoint (TCP)."""
        if self.token is not None:
            ipc.remove_endpoint(self.settings.data_dir)
        elif os.path.exists(self.socket_path):
            try: os.unlink(self.socket_path)
            except Exception: pass


if __name__ == "__main__":
    service = AuthService()
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()
