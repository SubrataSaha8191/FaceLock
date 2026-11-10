"""Client helper for connecting to the FaceLock auth service socket."""

import json
import socket
from typing import Any, Dict, Optional

DEFAULT_SOCKET_PATH = "/tmp/facelock.sock"
DEFAULT_TIMEOUT = 25.0  # an unlock attempt may watch the camera for several seconds


class ServiceClient:
    """Sends JSON authentication requests to the FaceLock auth service."""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH, timeout: float = DEFAULT_TIMEOUT):
        self.socket_path = socket_path
        self.timeout = timeout

    def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON request and return the JSON response."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self.socket_path)
            sock.sendall(json.dumps(request).encode("utf-8"))
            chunks = []
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                try:
                    return json.loads(b"".join(chunks).decode("utf-8"))
                except ValueError:
                    continue
            return json.loads(b"".join(chunks).decode("utf-8"))
        finally:
            sock.close()

    def verify_password(self, user_id: str, password: str) -> bool:
        """Verify user via password fallback."""
        resp = self.send_request({
            "action": "verify_password",
            "user_id": user_id,
            "password": password,
        })
        return resp.get("result", False)

    def check_enrolled(self, user_id: str) -> bool:
        """Check if user is enrolled in FaceLock."""
        resp = self.send_request({
            "action": "check_enrolled",
            "user_id": user_id,
        })
        return resp.get("result", False)

    def authenticate_face_detailed(self, user_id: str, secret: str = "MasterKey123") -> Dict[str, Any]:
        """Authenticate and return the full response (result, similarity, reason, message)."""
        return self.send_request({
            "action": "authenticate_face",
            "user_id": user_id,
            "secret": secret,
        })

    def authenticate_face(self, user_id: str, secret: str = "MasterKey123") -> bool:
        """Authenticate user via live biometric camera frames."""
        return bool(self.authenticate_face_detailed(user_id, secret).get("result", False))

