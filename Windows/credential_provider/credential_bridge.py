"""Python-side bridge for a future Windows Credential Provider.

A Credential Provider is a native COM DLL (C++ or C#) that Windows loads into the
sign-in UI. It cannot run Python itself, so the DLL launches this script as a child
process and reads the exit code.

Usage:
    credential_bridge.py --face <username>                 face check via the running service
    credential_bridge.py --password <username>             passphrase read from stdin
    credential_bridge.py <username> <password>             legacy form (password on the command line)

Exit codes:
    0  verified
    1  denied
    2  FaceLock service not reachable

The script talks to the same local service as the dashboard and SDK. On Windows that
is loopback TCP with a per-user token read from ``%LOCALAPPDATA%\\FaceLock\\endpoint.json``;
set ``FACELOCK_DATA_DIR`` to point at another user's folder when the bridge runs as SYSTEM.
"""

import sys
from pathlib import Path
from typing import Tuple

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Service.auth.service_client import ServiceClient

EXIT_OK, EXIT_DENIED, EXIT_UNAVAILABLE = 0, 1, 2


def verify_windows_user(username: str, password: str) -> bool:
    """Verify the fallback passphrase via the FaceLock service."""
    try:
        return bool(ServiceClient().verify_password(username, password))
    except Exception:
        return False


def verify_windows_face(username: str) -> Tuple[bool, str]:
    """Run a face unlock for ``username``. Returns ``(ok, reason)``; reason is
    ``service_unavailable`` when the service can't be reached."""
    try:
        resp = ServiceClient().authenticate_face_detailed(username)
    except (OSError, ValueError):
        return False, "service_unavailable"
    return bool(resp.get("result")), str(resp.get("reason", "match" if resp.get("result") else "denied"))


def main(argv) -> int:
    if len(argv) >= 3 and argv[1] == "--face":
        ok, reason = verify_windows_face(argv[2])
        if reason == "service_unavailable":
            return EXIT_UNAVAILABLE
        return EXIT_OK if ok else EXIT_DENIED
    if len(argv) >= 3 and argv[1] == "--password":
        password = sys.stdin.readline().rstrip("\r\n")
        return EXIT_OK if verify_windows_user(argv[2], password) else EXIT_DENIED
    if len(argv) >= 3 and not argv[1].startswith("--"):
        return EXIT_OK if verify_windows_user(argv[1], argv[2]) else EXIT_DENIED
    print(__doc__)
    return EXIT_DENIED


if __name__ == "__main__":
    sys.exit(main(sys.argv))
