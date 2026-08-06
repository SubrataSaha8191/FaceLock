#!/usr/bin/env python3
"""PAM helper script for FaceLock biometric & OS authentication.

Invoked by Linux PAM via pam_exec.so for sudo, GDM lock screen,
LightDM, and Polkit application authorization gates.

Exit codes:
    0 — Authentication successful (PAM_SUCCESS)
    1 — Authentication failed (PAM_AUTH_ERR)
    2 — Service unavailable (Fallback to system auth)
"""

import getpass
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Service.auth.service_client import ServiceClient

SOCKET_PATH = "/tmp/facelock.sock"


def main() -> int:
    """Execute PAM biometric & OS authentication flow."""
    user = _get_pam_user()
    if not user:
        return 1

    client = ServiceClient(SOCKET_PATH)

    try:
        if not client.check_enrolled(user):
            # User not enrolled in FaceLock — skip (allow system auth fallback)
            return 0

        # Attempt 1: Live Biometric Camera Face Verification
        if client.authenticate_face(user):
            return 0

        # Attempt 2: Password Fallback
        password = _get_password()
        if password and client.verify_password(user, password):
            return 0

        return 1

    except ConnectionRefusedError:
        return 2
    except Exception:
        return 2


def _get_pam_user() -> str:
    """Read PAM_USER from environment or fallback to current user."""
    return os.environ.get("PAM_USER", getpass.getuser())


def _get_password() -> str:
    """Read password from stdin if piped by PAM."""
    try:
        return sys.stdin.readline().strip()
    except EOFError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
