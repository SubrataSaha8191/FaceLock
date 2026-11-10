"""Desktop file interceptor: wraps .desktop launchers with the FaceLock app gate (Linux).

Protecting an app writes a per-user override in ``~/.local/share/applications`` whose
``Exec`` runs ``facelock-app-gate --cmd <original command>``. The override must be a *valid*
desktop entry or GNOME silently ignores it, so this module:

* keeps key names exactly as written (desktop-entry keys are case-sensitive)
* wraps the main ``Exec`` and the ``Exec`` of every ``[Desktop Action ...]`` (e.g. "New Window")
* turns off ``DBusActivatable`` (which lets the shell start the app without running ``Exec``)
* passes ``%u %U %f %F`` through, so opening links and files still works
* picks the launcher whose command matches exactly (a Chrome web app is not "Google Chrome")
"""

import configparser
import glob
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

GATE_SCRIPT = Path(__file__).resolve().parent / "bin" / "facelock-app-gate"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_APPS = Path.home() / ".local" / "share" / "applications"
BACKUP_DIR = Path.home() / ".facelock" / "desktop_backups"
SEARCH_DIRS = ["/usr/share/applications", str(Path.home() / ".local/share/applications"),
               "/var/lib/snap/desktop/applications", "/var/lib/flatpak/exports/share/applications"]
MARKER = "X-FaceLock-Protected"
ORIGINAL = "X-FaceLock-OriginalExec"
_PASSTHROUGH_CODES = ("%u", "%U", "%f", "%F")
_ENTRY = "Desktop Entry"


# ───────────────────────────── parsing helpers ─────────────────────────────

def _parser() -> configparser.RawConfigParser:
    cp = configparser.RawConfigParser(interpolation=None, strict=False, delimiters=("=",))
    cp.optionxform = str  # keep key case: "Exec" must stay "Exec"
    return cp


def _read(path) -> Optional[configparser.RawConfigParser]:
    cp = _parser()
    try:
        cp.read(str(path), encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return None
    return cp if cp.has_section(_ENTRY) else None


def _is_ours(path) -> bool:
    """True for files we wrote, including ones written by older versions with lowercased keys."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return re.search(r"^\s*x-facelock-protected\s*=\s*true\s*$", text, re.I | re.M) is not None


def _original_exec(cp: configparser.RawConfigParser) -> str:
    """The launcher's real command (the saved original if this is one of our overrides)."""
    for key in cp.options(_ENTRY):
        if key.lower() == ORIGINAL.lower():
            return cp.get(_ENTRY, key)
    return cp.get(_ENTRY, "Exec", fallback="")


def _tokens(exec_line: str) -> List[str]:
    try:
        return shlex.split(exec_line)
    except ValueError:
        return exec_line.split()


def _clean(exec_line: str) -> str:
    """The command without field codes (%U etc.), shell-quoted."""
    return shlex.join(t for t in _tokens(exec_line) if not t.startswith("%"))


def _codes(exec_line: str) -> List[str]:
    return [t for t in _tokens(exec_line) if t in _PASSTHROUGH_CODES]


def _dq(arg: str) -> str:
    """Quote one argument for a desktop-entry ``Exec`` line."""
    if re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]+", arg):
        return arg
    return '"' + re.sub(r'(["`$\\])', r"\\\1", arg) + '"'


def _gate_exec(original_exec: str) -> str:
    python = sys.executable or "python3"
    line = f"{_dq(python)} {_dq(str(GATE_SCRIPT))} --cmd {_dq(_clean(original_exec))}"
    codes = _codes(original_exec)
    return f"{line} -- {' '.join(codes)}" if codes else line


# ───────────────────────────── locating the launcher ─────────────────────────────

def _candidates() -> List[Tuple[Path, str]]:
    """(source file, original Exec) for every launcher we could protect, in search order."""
    out: List[Tuple[Path, str]] = []
    for d in SEARCH_DIRS:
        for f in sorted(glob.glob(os.path.join(d, "*.desktop"))):
            fp = Path(f)
            if fp.name.startswith("facelock-"):
                continue
            source = fp
            if _is_ours(fp):
                backup = BACKUP_DIR / fp.name
                if not backup.exists():
                    continue            # our override of a system launcher: the system file is the source
                source = backup         # our override of a user launcher: restore from its backup
            cp = _read(source)
            if cp is None:
                continue
            ex = _original_exec(cp)
            if ex:
                out.append((source, ex))
    return out


def _score(target_cmd: str, exec_line: str) -> int:
    want, have = _tokens(_clean(target_cmd)), _tokens(_clean(exec_line))
    if not want or not have:
        return 0
    if want == have:
        return 3
    if len(want) == 1 and os.path.basename(want[0]) == os.path.basename(have[0]):
        return 2                         # bare command vs. the same program with arguments
    if len(want) == 1 and os.path.basename(want[0]) in os.path.basename(have[0]):
        return 1
    return 0


def _find_desktop_files(cmd: str) -> List[Path]:
    """Every launcher for a command. All exact matches count (a distro can ship two launchers for
    one program, and the dock may pin either); otherwise the single best looser match."""
    scored = [(_score(cmd, ex), src) for src, ex in _candidates()]
    top = max((sc for sc, _ in scored), default=0)
    if top == 0:
        return []
    if top == 3:
        return [src for sc, src in scored if sc == 3]
    return [next(src for sc, src in scored if sc == top)]


def _find_desktop_file(cmd: str) -> Optional[Path]:
    files = _find_desktop_files(cmd)
    return files[0] if files else None


# ───────────────────────────── install / uninstall ─────────────────────────────

def install_gate(app_name: str, cmd: str) -> bool:
    """Write valid overrides that run ``cmd`` through the gate. Safe to call repeatedly."""
    if not sys.platform.startswith("linux"):
        return False
    sources = _find_desktop_files(cmd)
    if not sources:
        return False
    LOCAL_APPS.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    done = False
    for src in sources:
        done = _write_override(src) or done
    if done:
        _refresh_desktop_db()
    return done


def _write_override(src: Path) -> bool:
    target = LOCAL_APPS / src.name
    # Keep the user's own launcher (a Chrome web app, say) so it can be restored later.
    if target.exists() and not _is_ours(target) and not (BACKUP_DIR / src.name).exists():
        shutil.copy2(str(target), str(BACKUP_DIR / src.name))

    cp = _read(src)
    if cp is None:
        return False
    original = _original_exec(cp)
    cp.set(_ENTRY, "Exec", _gate_exec(original))
    cp.set(_ENTRY, "DBusActivatable", "false")      # otherwise the shell can skip Exec entirely
    cp.set(_ENTRY, MARKER, "true")
    cp.set(_ENTRY, ORIGINAL, original)
    for section in cp.sections():
        if section.startswith("Desktop Action ") and cp.has_option(section, "Exec"):
            action_exec = cp.get(section, "Exec")
            cp.set(section, "Exec", _gate_exec(action_exec))
            cp.set(section, ORIGINAL, action_exec)

    tmp = target.with_suffix(".desktop.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        cp.write(fh, space_around_delimiters=False)
    os.replace(tmp, target)
    return True


def uninstall_gate(cmd: str) -> bool:
    """Remove every override for the command, restoring the original launchers."""
    if not sys.platform.startswith("linux"):
        return False
    targets = _find_protected_files(cmd)
    if not targets:
        return False
    for target in targets:
        backup = BACKUP_DIR / target.name
        if backup.exists():
            shutil.copy2(str(backup), str(target))
            backup.unlink()
        else:
            target.unlink(missing_ok=True)
    _refresh_desktop_db()
    return True


def _find_protected_files(cmd: str) -> List[Path]:
    """Our overrides in the user's launcher folder that wrap this command."""
    scored: List[Tuple[int, Path]] = []
    for f in sorted(glob.glob(str(LOCAL_APPS / "*.desktop"))):
        if not _is_ours(f):
            continue
        cp = _read(f)
        if cp is not None:
            scored.append((_score(cmd, _original_exec(cp)), Path(f)))
    top = max((sc for sc, _ in scored), default=0)
    if top == 0:
        return []
    return [p for sc, p in scored if sc == top] if top == 3 else [next(p for sc, p in scored if sc == top)]


def is_protected(cmd: str) -> bool:
    return bool(_find_protected_files(cmd))


def _refresh_desktop_db() -> None:
    tool = shutil.which("update-desktop-database")
    if tool:
        try:
            subprocess.run([tool, str(LOCAL_APPS)], capture_output=True, timeout=15)
        except Exception:
            pass


def ensure_autostart() -> bool:
    """Install an XDG autostart entry for the FaceLock auth service daemon."""
    if not sys.platform.startswith("linux"):
        return False
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
