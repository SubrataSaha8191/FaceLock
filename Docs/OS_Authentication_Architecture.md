# FaceLock OS Authentication Architecture

This document explains the technical implementation of FaceLock's system-wide biometric OS authentication from scratch.

## 1. Core Concept: Pluggable Authentication Modules (PAM)
Linux manages authentication centrally through PAM (`/etc/pam.d/`). Whenever a user attempts to run `sudo`, unlock the GDM screen, or authorize an action via Polkit, the OS consults the corresponding PAM configuration stack.

To integrate FaceLock, we inject a custom PAM rule at the top of these stacks:
`auth sufficient pam_exec.so quiet /path/to/python3 /path/to/pam_facelock.py`

- `sufficient`: If FaceLock succeeds, authentication is immediately granted, bypassing the password prompt.
- `pam_exec.so`: A built-in PAM module that executes an external script for authentication.
- `quiet`: Ensures that if the script fails (e.g., face mismatch), it fails silently without printing error exit codes to the GDM UI, allowing the system to seamlessly fall back to standard password entry.

## 2. The PAM Helper Script (`pam_facelock.py`)
This script acts as the bridge between the OS authentication request and the FaceLock system.

- It reads the user requesting authentication via the `PAM_USER` environment variable.
- It cannot access the camera directly because it runs under various user contexts (e.g., `gdm`, `root`, or normal users), which leads to permission issues with video devices.
- Therefore, it connects to a local Unix Domain Socket (`/tmp/facelock.sock`) and sends an RPC request (`{"action": "authenticate_face", "user_id": "..."}`) to the FaceLock background daemon.
- It exits with `0` on success or `1` on failure, signaling PAM to either grant access or proceed to the next module (password).

## 3. The Background Daemon (`facelock.service` and `auth_service.py`)
To solve permission, resource, and latency issues, FaceLock runs as a persistent systemd daemon (`User=root`).

- **Camera Permissions**: Running as root ensures the service always has access to `/dev/video*` regardless of which user initiates the auth request.
- **Resource Management**: It holds the authentication engine in memory and avoids the overhead of loading ML models on every single `sudo` command.
- **Socket Communication**: It listens on `/tmp/facelock.sock` with read/write permissions open to everyone (`0o666`), allowing the `pam_exec` script to communicate with it.
- **Data Directory Resolution**: It dynamically resolves the database path to the enrolling user's `.facelock` directory, avoiding mismatched databases when running under root.

## 4. Application Protection (`facelock-app-gate`)
For intercepting application launches (e.g., opening OBS from the launcher):
- We provide `desktop_interceptor.py`, which backs up original `.desktop` files in `/usr/share/applications/`.
- It rewrites the `Exec=` line to prepend our gate utility: `Exec=/path/to/facelock-app-gate --target "obs"`.
- The gate utility queries the same socket (`/tmp/facelock.sock`). If facial authentication fails, it presents a native GUI password prompt (using `zenity` or `kdialog`) instead of hanging in a terminal.

## 5. The Installer (`install_pam.sh`)
The shell installer automates the deployment:
1. Creates the systemd unit file (`/etc/systemd/system/facelock.service`) with the correct environment variables.
2. Starts and enables the daemon to run on boot.
3. Injects the `pam_exec.so` rule into `/etc/pam.d/sudo`, `/etc/pam.d/gdm-password`, `/etc/pam.d/lightdm`, and `/etc/pam.d/polkit-1`.

## 6. Security and Fallback
- **Liveness Detection**: Prevents spoofing attacks using printed photos or screens.
- **Seamless Fallback**: If the camera is unavailable, the environment is too dark, or the face isn't recognized, the script gracefully exits with `1`, and the OS falls back to traditional password authentication without hanging.
