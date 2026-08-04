# Phase 4: OS Authentication Integration

## Overview
Phase 4 connects FaceLock to operating system authentication via a background socket service, Linux PAM module, and Windows Credential Provider bridge.

## Architecture

```text
 ┌───────────────┐     ┌───────────────┐
 │  Linux PAM    │     │  Windows CP   │
 │  (pam_exec)   │     │  (COM DLL)    │
 └──────┬────────┘     └──────┬────────┘
        │                     │
        ▼                     ▼
 ┌─────────────────────────────────────┐
 │      pam_facelock.py   │   credential_bridge.py
 └──────────────┬──────────────────────┘
                │  UNIX Domain Socket
                ▼
 ┌─────────────────────────────────────┐
 │      Auth Service Daemon            │
 │      (Service/auth/auth_service.py) │
 └──────────────┬──────────────────────┘
                │
                ▼
 ┌─────────────────────────────────────┐
 │      Core Authentication Engine     │
 └─────────────────────────────────────┘
```

## Service Protocol

The auth service listens on `/tmp/facelock.sock` and accepts JSON requests:

### verify_password
```json
{"action": "verify_password", "user_id": "alice", "password": "SecureP@ss1"}
→ {"result": true, "message": "Password verified"}
```

### check_enrolled
```json
{"action": "check_enrolled", "user_id": "alice"}
→ {"result": true, "message": "enrollment_check"}
```

## Linux PAM Flow
1. User runs `sudo` or logs in.
2. PAM invokes `pam_facelock.py` via `pam_exec.so`.
3. Script sends credentials to auth service socket.
4. Exit code 0 = pass, 1 = fail, 2 = service unavailable (fallthrough).

## systemd Service
Located at `Linux/systemd/facelock.service`. Runs the auth service as a persistent daemon.
