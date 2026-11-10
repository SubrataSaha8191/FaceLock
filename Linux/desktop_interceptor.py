"""Desktop file interceptor — wraps .desktop Exec lines with FaceLock gate."""

import configparser, glob, os, shutil, sys
from pathlib import Path

GATE_SCRIPT = Path(__file__).resolve().parent / "bin" / "facelock-app-gate"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_APPS = Path.home() / ".local" / "share" / "applications"
BACKUP_DIR = Path.home() / ".facelock" / "desktop_backups"
SEARCH_DIRS = ["/usr/share/applications", str(Path.home() / ".local/share/applications"),
               "/var/lib/snap/desktop/applications", "/var/lib/flatpak/exports/share/applications"]
MARKER = "X-FaceLock-Protected"


def _find_desktop_file(cmd: str) -> Path | None:
    """Locate the original .desktop file matching a command string."""
    base_cmd = cmd.split()[0].split("/")[-1]
    for d in SEARCH_DIRS:
        for f in glob.glob(os.path.join(d, "*.desktop")):
            fp = Path(f)
            if fp.name.startswith("facelock-"): continue
            try:
                cp = configparser.ConfigParser(interpolation=None)
                cp.read(f, encoding="utf-8")
                ex = cp.get("Desktop Entry", "Exec", fallback="")
                if base_cmd in ex.split()[0].split("/")[-1]:
                    return fp
            except Exception: pass
    return None


def install_gate(app_name: str, cmd: str) -> bool:
    """Create a .desktop override that wraps cmd with facelock-app-gate."""
    if not sys.platform.startswith("linux"): return False
    src = _find_desktop_file(cmd)
    if not src: return False
    LOCAL_APPS.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Backup original if it's in the local dir (user override already exists)
    target = LOCAL_APPS / src.name
    if target.exists() and not _is_facelock_file(target):
        shutil.copy2(str(target), str(BACKUP_DIR / src.name))

    cp = configparser.ConfigParser(interpolation=None)
    cp.read(str(src), encoding="utf-8")
    original_exec = cp.get("Desktop Entry", "Exec", fallback="")
    # Strip field codes like %U %F from original exec for the gate --cmd
    clean_cmd = " ".join(a for a in original_exec.split() if not a.startswith("%"))
    python = sys.executable or "python3"
    gate_exec = f"{python} {GATE_SCRIPT} --cmd \"{clean_cmd}\""
    cp.set("Desktop Entry", "Exec", gate_exec)
    cp.set("Desktop Entry", MARKER, "true")
    cp.set("Desktop Entry", "X-FaceLock-OriginalExec", original_exec)

    with open(str(target), "w", encoding="utf-8") as fh:
        cp.write(fh)
    _refresh_desktop_db()
    return True


def uninstall_gate(cmd: str) -> bool:
    """Remove the .desktop override, restoring the original launcher."""
    if not sys.platform.startswith("linux"): return False
    src = _find_desktop_file_by_marker(cmd)
    if not src: return False
    backup = BACKUP_DIR / src.name
    if backup.exists():
        shutil.copy2(str(backup), str(src))
        backup.unlink()
    else:
        src.unlink(missing_ok=True)
    _refresh_desktop_db()
    return True


def _find_desktop_file_by_marker(cmd: str) -> Path | None:
    """Find our FaceLock-overridden .desktop file in local apps."""
    base_cmd = cmd.split()[0].split("/")[-1]
    for f in glob.glob(str(LOCAL_APPS / "*.desktop")):
        try:
            cp = configparser.ConfigParser(interpolation=None)
            cp.read(f, encoding="utf-8")
            if cp.get("Desktop Entry", MARKER, fallback="") == "true":
                orig = cp.get("Desktop Entry", "X-FaceLock-OriginalExec", fallback="")
                if base_cmd in orig:
                    return Path(f)
        except Exception: pass
    return None


def _is_facelock_file(p: Path) -> bool:
    try:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(str(p), encoding="utf-8")
        return cp.get("Desktop Entry", MARKER, fallback="") == "true"
    except Exception: return False


def _refresh_desktop_db():
    try: os.system("update-desktop-database ~/.local/share/applications 2>/dev/null")
    except Exception: pass


def ensure_autostart() -> bool:
    """Install an XDG autostart entry for the FaceLock auth service daemon."""
    if not sys.platform.startswith("linux"): return False
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    entry = autostart_dir / "facelock-daemon.desktop"
    python = sys.executable or "python3"
    svc_path = PROJECT_ROOT / "Service" / "auth" / "auth_service.py"
    content = f"""[Desktop Entry]
Type=Application
Name=FaceLock Auth Daemon
Comment=Background biometric authentication service
Exec={python} {svc_path}
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
X-FaceLock-Daemon=true
"""
    entry.write_text(content, encoding="utf-8")
    return True
