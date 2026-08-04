"""Windows Credential Provider bridge stub for FaceLock.

This module provides the Python-side bridge for a future Windows
Credential Provider DLL. The DLL would call this script to verify
the user's identity against the FaceLock auth service.

Note: Full Windows integration requires a C++ COM DLL built on Windows.
This stub demonstrates the protocol and can be tested against the
auth service socket when running under WSL or a UNIX-compatible layer.
"""

import sys
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Service.auth.service_client import ServiceClient

SOCKET_PATH = "/tmp/facelock.sock"


def verify_windows_user(username: str, password: str) -> bool:
    """Verify user credentials via FaceLock auth service.

    Args:
        username: Windows login username (mapped to FaceLock user_id).
        password: User password for fallback authentication.

    Returns:
        True if authentication succeeds, False otherwise.
    """
    client = ServiceClient(SOCKET_PATH)
    try:
        return client.verify_password(username, password)
    except Exception:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: credential_bridge.py <username> <password>")
        sys.exit(1)
    result = verify_windows_user(sys.argv[1], sys.argv[2])
    sys.exit(0 if result else 1)
