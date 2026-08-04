# Linux PAM Configuration Guide for FaceLock

## Prerequisites

1. FaceLock auth service must be running:
   ```bash
   sudo systemctl start facelock
   ```

2. User must be enrolled via the Dashboard or CLI.

## PAM Configuration

### sudo Authentication

Add to `/etc/pam.d/sudo` **before** the existing `@include` lines:

```text
auth    sufficient    pam_exec.so expose_authtok /opt/facelock/Linux/pam/pam_facelock.py
```

### Login Screen

Add to `/etc/pam.d/login`:

```text
auth    sufficient    pam_exec.so expose_authtok /opt/facelock/Linux/pam/pam_facelock.py
```

## systemd Service

### Install

```bash
sudo cp Linux/systemd/facelock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable facelock
sudo systemctl start facelock
```

### Status

```bash
sudo systemctl status facelock
```

## How It Works

1. PAM invokes `pam_facelock.py` via `pam_exec.so`.
2. The script connects to `/tmp/facelock.sock`.
3. It sends the user's credentials to the FaceLock auth service.
4. Exit code `0` = success, `1` = failure, `2` = service unavailable (falls through to next PAM module).
