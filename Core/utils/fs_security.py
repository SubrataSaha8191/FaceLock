"""Best-effort "owner only" permissions that work on POSIX and Windows."""

import os
import subprocess
from pathlib import Path


def restrict_to_owner(path) -> bool:
    """Limit a file to the current user. Returns True when the restriction was applied.

    POSIX: chmod 0600. Windows: remove inherited ACLs and grant only the current
    user (via icacls). Failures are swallowed; callers must not depend on this for
    correctness, only for defence in depth.
    """
    p = str(path)
    if not os.path.exists(p):
        return False
    try:
        if os.name == "nt":
            user = os.environ.get("USERNAME")
            if not user:
                return False
            domain = os.environ.get("USERDOMAIN")
            account = f"{domain}\\{user}" if domain else user
            res = subprocess.run(
                ["icacls", p, "/inheritance:r", "/grant:r", f"{account}:F"],
                capture_output=True, timeout=10,
            )
            return res.returncode == 0
        os.chmod(p, 0o600)
        return True
    except Exception:
        return False
