# FaceLock on Windows

Windows support is **early**. The recognition core, the unlock service, the dashboard backend and the SDK work on Windows Python. Signing in to Windows itself with your face does not (see [What is not available](#what-is-not-available)).

## What works

| Piece | Status |
|---|---|
| Face recognition, enrollment, encrypted storage, password fallback | Works. Same scores as Linux in testing |
| Unlock service | Works. Listens on `127.0.0.1` only; every request needs a per-user token |
| Python SDK (`facelock_dev`) | Works with no changes to your code |
| Dashboard | Runs through the system WebView2 (Edge) instead of Qt. Not yet tried on a real Windows machine |
| Camera | Opened through DirectShow. Not yet tried on a real Windows machine |
| Installer scripts | Written, not yet run on a real Windows machine |

**How it was tested:** the test suites (105 FaceLock tests, 14 SDK tests) and an end-to-end run (real service, real models, SDK calling it, rejection of an unknown face and of a request without the token) were run on Windows Python 3.12 under Wine. Wine is not Windows: it cannot test a real webcam, WebView2, PowerShell, or Windows file permissions.

## Install

Needs Python 3.9 or newer.

```powershell
powershell -ExecutionPolicy Bypass -File Windows\install_windows.ps1
```

This creates `.venv`, installs FaceLock, downloads the face models, adds **FaceLock** to the Start Menu and starts the unlock service now and at every sign-in. Add `-NoAutostart` to skip the service startup entry.

Then open **FaceLock** from the Start Menu, enroll your face and use **Unlock → Test unlock**.

Remove it with:

```powershell
powershell -ExecutionPolicy Bypass -File Windows\uninstall_windows.ps1            # keeps your face data
powershell -ExecutionPolicy Bypass -File Windows\uninstall_windows.ps1 -RemoveData
```

## How it differs from Linux

| | Linux | Windows |
|---|---|---|
| Service ↔ client | UNIX socket `/tmp/facelock.sock` | Loopback TCP + secret token |
| Where the client finds the service | Fixed socket path | `%LOCALAPPDATA%\FaceLock\endpoint.json` (port and token) |
| Data folder | `~/.facelock` | `%LOCALAPPDATA%\FaceLock` |
| Window | Qt | System WebView2 |
| Service startup | systemd | Startup-folder shortcut |
| Camera | V4L2 | DirectShow |

`endpoint.json` is created fresh each time the service starts and removed when it stops. It is restricted to your user account. Environment variables: `FACELOCK_SOCKET` (address or `auto`), `FACELOCK_TOKEN`, `FACELOCK_DATA_DIR`.

Logs go to `%LOCALAPPDATA%\FaceLock\facelock.log` when the service runs without a console.

## What is not available

- **Sign-in screen / lock screen unlock.** This needs a Windows *Credential Provider*, a native COM DLL (C++ or C#) that Windows loads into the sign-in UI, and a way to reach the camera from there. The current service runs in your own session, so it can only help once you are signed in. `credential_provider/credential_bridge.py` is the Python half of that design (the DLL would run it and read its exit code); the DLL itself does not exist.
- **Protected apps** (the launcher gate) and the `sudo` equivalent.
- Scanning the Start Menu for apps to protect.

## The Credential Provider bridge

```text
credential_bridge.py --face <username>        # face check via the running service
credential_bridge.py --password <username>    # passphrase read from stdin
```

Exit codes: `0` verified, `1` denied, `2` service not reachable. When it runs as SYSTEM, set `FACELOCK_DATA_DIR` to the signed-in user's `%LOCALAPPDATA%\FaceLock` so it can find `endpoint.json`.

## Files

```text
Windows/
  README.md                 this guide
  install_windows.ps1       per-user installer
  uninstall_windows.ps1     removes shortcuts, stops the service
  credential_provider/
    credential_bridge.py    Python side of a future Credential Provider
```
