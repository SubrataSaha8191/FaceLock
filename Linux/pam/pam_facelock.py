#!/usr/bin/env python3
"""PAM helper script for FaceLock biometric & OS authentication.

Invoked by Linux PAM via pam_exec.so for sudo, GDM lock screen,
LightDM, and Polkit application authorization gates.

Exit codes:
    0 — Authentication successful (Face matched, skip password prompt)
    1 — Authentication failed or skipped (Fallback to default OS password)
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
            return 1

        # Attempt: Live Biometric Camera Face Verification
        if client.authenticate_face(user):
            return 0  # Face unlock successful! Skip password prompt.

        return 1  # Face match failed -> Fallback to default OS password prompt

    except Exception:
        return 1  # Service unavailable -> Fallback to default OS password prompt


def _get_pam_user() -> str:
    """Read PAM_USER from environment or fallback to current user."""
    return os.environ.get("PAM_USER", getpass.getuser())


if __name__ == "__main__":
    sys.exit(main())
