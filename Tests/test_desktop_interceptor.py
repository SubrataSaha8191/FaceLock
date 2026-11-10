"""App-gate launcher overrides must be valid desktop entries that GNOME will honour."""

import configparser
import importlib.machinery
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from Linux import desktop_interceptor as di

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux launchers only")

CHROME = """[Desktop Entry]
Version=1.0
Name=Google Chrome
GenericName=Web Browser
Exec=/usr/bin/google-chrome-stable %U
Icon=google-chrome
Type=Application
DBusActivatable=true
StartupWMClass=google-chrome
Actions=new-window;new-private-window;

[Desktop Action new-window]
Name=New Window
Exec=/usr/bin/google-chrome-stable

[Desktop Action new-private-window]
Name=New Incognito Window
Exec=/usr/bin/google-chrome-stable --incognito
"""
OBS = "[Desktop Entry]\nName=OBS Studio\nExec=obs\nIcon=obs\nType=Application\n"
WEBAPP = ("[Desktop Entry]\nType=Application\nName=WhatsApp Web\n"
          "Exec=/opt/google/chrome/google-chrome --profile-directory=Default --app-id=abc123\n")
APP_CMD = "/opt/google/chrome/google-chrome --profile-directory=Default --app-id=abc123"


@pytest.fixture
def env(tmp_path, monkeypatch):
    system, local, backups = tmp_path / "system", tmp_path / "local", tmp_path / "backups"
    system.mkdir(); local.mkdir()
    (system / "google-chrome.desktop").write_text(CHROME)
    (system / "com.obsproject.Studio.desktop").write_text(OBS)
    (local / "chrome-abc123-Default.desktop").write_text(WEBAPP)
    monkeypatch.setattr(di, "SEARCH_DIRS", [str(system), str(local)])
    monkeypatch.setattr(di, "LOCAL_APPS", local)
    monkeypatch.setattr(di, "BACKUP_DIR", backups)
    monkeypatch.setattr(di, "_refresh_desktop_db", lambda: None)
    return system, local, backups


def parse(path):
    cp = configparser.RawConfigParser(interpolation=None, strict=False, delimiters=("=",))
    cp.optionxform = str
    cp.read(path, encoding="utf-8")
    return cp


def test_override_keeps_key_case_and_wraps_exec(env):
    _, local, _ = env
    assert di.install_gate("Chrome", "/usr/bin/google-chrome-stable") is True
    entry = parse(local / "google-chrome.desktop")["Desktop Entry"]
    assert "Exec" in entry and "exec" not in entry and "Name" in entry and "Type" in entry   # the old bug
    assert "facelock-app-gate" in entry["Exec"] and "--cmd /usr/bin/google-chrome-stable" in entry["Exec"]
    assert entry["Exec"].endswith("-- %U")                       # links/files still reach the app
    assert entry["DBusActivatable"] == "false"                  # the shell can't skip Exec
    assert entry["X-FaceLock-Protected"] == "true"


def test_menu_actions_are_gated_too(env):
    _, local, _ = env
    di.install_gate("Chrome", "/usr/bin/google-chrome-stable")
    cp = parse(local / "google-chrome.desktop")
    assert "facelock-app-gate" in cp["Desktop Action new-window"]["Exec"]
    assert "--incognito" in cp["Desktop Action new-private-window"]["Exec"]
    assert "facelock-app-gate" in cp["Desktop Action new-private-window"]["Exec"]


def test_every_launcher_for_the_same_command_is_protected(env):
    """Distros can ship two launchers for one program (com.google.Chrome + google-chrome); the dock may pin either."""
    system, local, _ = env
    (system / "com.google.Chrome.desktop").write_text(CHROME)
    assert di.install_gate("Chrome", "/usr/bin/google-chrome-stable") is True
    for name in ("google-chrome.desktop", "com.google.Chrome.desktop"):
        assert "facelock-app-gate" in parse(local / name)["Desktop Entry"]["Exec"], name
    assert di.uninstall_gate("/usr/bin/google-chrome-stable") is True
    assert not (local / "google-chrome.desktop").exists() and not (local / "com.google.Chrome.desktop").exists()


def test_web_app_is_matched_to_its_own_launcher_not_chrome(env):
    system, local, backups = env
    assert di._find_desktop_file(APP_CMD) == local / "chrome-abc123-Default.desktop"
    assert di._find_desktop_file("/usr/bin/google-chrome-stable") == system / "google-chrome.desktop"
    di.install_gate("WhatsApp", APP_CMD)
    assert not (local / "google-chrome.desktop").exists()           # Chrome itself untouched
    wa = parse(local / "chrome-abc123-Default.desktop")["Desktop Entry"]
    assert "facelock-app-gate" in wa["Exec"] and "--app-id=abc123" in wa["Exec"]
    assert (backups / "chrome-abc123-Default.desktop").read_text() == WEBAPP   # original preserved


def test_install_is_idempotent_and_never_backs_up_an_override(env):
    _, local, backups = env
    di.install_gate("WhatsApp", APP_CMD)
    first = (local / "chrome-abc123-Default.desktop").read_text()
    di.install_gate("WhatsApp", APP_CMD)
    assert (local / "chrome-abc123-Default.desktop").read_text() == first
    assert (backups / "chrome-abc123-Default.desktop").read_text() == WEBAPP


def test_uninstall_restores_user_launcher_and_removes_system_override(env):
    _, local, backups = env
    di.install_gate("WhatsApp", APP_CMD)
    di.install_gate("OBS", "obs")
    assert di.is_protected(APP_CMD) and di.is_protected("obs")
    assert di.uninstall_gate(APP_CMD) is True
    assert (local / "chrome-abc123-Default.desktop").read_text() == WEBAPP
    assert not (backups / "chrome-abc123-Default.desktop").exists()
    assert di.uninstall_gate("obs") is True
    assert not (local / "com.obsproject.Studio.desktop").exists()


def test_broken_lowercase_override_from_old_versions_is_repaired(env):
    _, local, _ = env
    broken = ("[Desktop Entry]\nname = OBS Studio\nexec = python gate --cmd \"obs\"\ntype = Application\n"
              "x-facelock-protected = true\nx-facelock-originalexec = obs\n")
    (local / "com.obsproject.Studio.desktop").write_text(broken)
    assert di.is_protected("obs")                       # recognised as ours despite the bad case
    assert di.install_gate("OBS", "obs") is True        # regenerated from the system launcher
    entry = parse(local / "com.obsproject.Studio.desktop")["Desktop Entry"]
    assert "Exec" in entry and "exec" not in entry and entry["Name"] == "OBS Studio"


def test_unknown_command_is_not_reported_as_protected(env):
    assert di.install_gate("Nope", "/usr/bin/does-not-exist") is False


@pytest.mark.skipif(shutil.which("desktop-file-validate") is None, reason="desktop-file-validate not installed")
def test_generated_files_pass_the_real_validator(env):
    _, local, _ = env
    for name, cmd in (("Chrome", "/usr/bin/google-chrome-stable"), ("OBS", "obs"), ("WhatsApp", APP_CMD)):
        di.install_gate(name, cmd)
    for f in local.glob("*.desktop"):
        res = subprocess.run(["desktop-file-validate", str(f)], capture_output=True, text=True)
        errors = [l for l in res.stdout.splitlines() + res.stderr.splitlines() if "error:" in l]
        assert not errors, f"{f.name}: {errors}"


def test_gate_passes_launcher_arguments_through():
    gate = Path(__file__).resolve().parent.parent / "Linux" / "bin" / "facelock-app-gate"
    loader = importlib.machinery.SourceFileLoader("facelock_app_gate", str(gate))
    spec = importlib.util.spec_from_loader("facelock_app_gate", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    assert mod.build_command("obs", []) == "obs"
    assert mod.build_command("google-chrome", ["https://a.b/?x=1&y=2"]) == "google-chrome 'https://a.b/?x=1&y=2'"
