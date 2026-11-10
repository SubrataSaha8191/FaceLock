"""Find an application's real icon (freedesktop icon themes, pixmaps, absolute paths)."""

import base64
import glob
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

_MIME = {".png": "image/png", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
_MAX_BYTES = 400_000


def default_search_dirs() -> List[str]:
    home = Path.home()
    return [
        str(home / ".local/share/icons"), str(home / ".icons"),
        "/usr/share/icons", "/usr/local/share/icons",
        str(home / ".local/share/flatpak/exports/share/icons"), "/var/lib/flatpak/exports/share/icons",
        "/var/lib/snapd/desktop/icons",
    ]


def _rank(path: str) -> float:
    """Prefer scalable art, then the largest raster up to 256px."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        return 1000.0
    sizes = [int(n) for n in re.findall(r"(\d{2,4})(?:x\d{2,4})?", path)]
    size = max((n for n in sizes if n <= 512), default=0)
    return float(size if size <= 256 else 256 - (size - 256) / 100.0)


class IconResolver:
    """Resolves icon names to data URIs. Results (including misses) are cached."""

    def __init__(self, search_dirs: Optional[Iterable[str]] = None, pixmaps: Optional[Iterable[str]] = None):
        self.dirs = [d for d in (search_dirs if search_dirs is not None else default_search_dirs()) if os.path.isdir(d)]
        self.pixmaps = list(pixmaps if pixmaps is not None else ["/usr/share/pixmaps"])
        self._cache: Dict[str, Optional[str]] = {}

    def find(self, name: str) -> Optional[str]:
        """Return a filesystem path for the icon, or None."""
        if not name:
            return None
        if os.path.isabs(name):
            return name if os.path.isfile(name) and os.path.splitext(name)[1].lower() in _MIME else None
        if "/" in name or ".." in name:
            return None
        candidates: List[str] = []
        for base in self.dirs:
            candidates += glob.glob(f"{base}/*/*/apps/{glob.escape(name)}.*")      # theme/48x48/apps/x.png
            candidates += glob.glob(f"{base}/*/apps/*/{glob.escape(name)}.*")      # theme/apps/48/x.svg
            candidates += glob.glob(f"{base}/*/*/{glob.escape(name)}.*")           # flat layouts
        for px in self.pixmaps:
            candidates += glob.glob(f"{px}/{glob.escape(name)}.*")
        usable = [c for c in candidates if os.path.splitext(c)[1].lower() in _MIME and os.path.isfile(c)
                  and os.path.getsize(c) <= _MAX_BYTES]
        return max(usable, key=_rank) if usable else None

    def data_uri(self, *names: str) -> Optional[str]:
        """First name that resolves, as a ``data:`` URI."""
        for name in names:
            if name in self._cache:
                uri = self._cache[name]
            else:
                uri = None
                path = self.find(name)
                if path:
                    try:
                        raw = Path(path).read_bytes()
                        uri = f"data:{_MIME[os.path.splitext(path)[1].lower()]};base64,{base64.b64encode(raw).decode()}"
                    except OSError:
                        uri = None
                self._cache[name] = uri
            if uri:
                return uri
        return None
