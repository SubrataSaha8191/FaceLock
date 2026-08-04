#!/usr/bin/env python3
"""PAM helper script for FaceLock biometric authentication.

This script is invoked by the PAM stack via pam_exec.so.
It connects to the FaceLock auth service socket and verifies
the user via password fallback.

Exit codes:
    0  — Authentication successful
    1  — Authentication failed
    2  — Service unavailable
"""

import getpass
import sys
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Service.auth.service_client import ServiceClient

SOCKET_PATH = "/tmp/facelock.sock"


def main() -> int:
    """Execute PAM authentication flow."""
    user = _get_pam_user()
    if not user:
        return 1

    client = ServiceClient(SOCKET_PATH)

    try:
        if not client.check_enrolled(user):
            # User not enrolled in FaceLock — skip (allow fallback to system auth)
            return 0

        password = _get_password()
        if not password:
            return 1

        if client.verify_password(user, password):
            return 0
        return 1

    except ConnectionRefusedError:
        # Service not running — allow system fallback
        return 2
    except Exception:
        return 2


def _get_pam_user() -> str:
    """Read PAM_USER from environment or fallback to current user."""
    import os
    return os.environ.get("PAM_USER", getpass.getuser())


def _get_password() -> str:
    """Read password from stdin (piped by PAM)."""
    try:
        return sys.stdin.readline().strip()
    except EOFError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
