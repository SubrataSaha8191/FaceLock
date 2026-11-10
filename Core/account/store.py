"""Persists the local profile, Google client settings and linked Google identity."""

import getpass
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class AccountStore:
    """JSON file in the data directory (mode 0600). Never stores OAuth tokens."""

    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / "account.json"

    def _read(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.path)

    # ---- public view (safe for the UI) ----
    def public(self) -> Dict[str, Any]:
        d = self._read()
        profile = d.get("profile") or None
        return {
            "localName": d.get("local_name") or getpass.getuser().replace("_", " ").title(),
            "google": profile,
            "hasClient": bool(d.get("google_client_id")),
            "clientId": d.get("google_client_id", ""),
            "hasSecret": bool(d.get("google_client_secret")),
        }

    def client(self) -> Dict[str, str]:
        d = self._read()
        return {"client_id": d.get("google_client_id", ""), "client_secret": d.get("google_client_secret", "")}

    def set_local_name(self, name: str) -> None:
        d = self._read()
        d["local_name"] = name.strip()[:60]
        self._write(d)

    def set_client(self, client_id: str, client_secret: Optional[str] = None) -> None:
        d = self._read()
        d["google_client_id"] = client_id.strip()
        if client_secret is not None:
            d["google_client_secret"] = client_secret.strip()
        self._write(d)

    def set_profile(self, profile: Optional[Dict[str, Any]]) -> None:
        d = self._read()
        if profile is None:
            d.pop("profile", None)
        else:
            d["profile"] = {k: profile.get(k, "") for k in ("sub", "name", "given_name", "email", "picture")}
        self._write(d)
