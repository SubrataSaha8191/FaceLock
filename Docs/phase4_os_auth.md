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

The auth service listens on `/tmp/facelock.sock` (Linux) or on `127.0.0.1` with a per-user token (Windows) and accepts JSON requests. On the TCP transport every request must include `"token"` from `endpoint.json`; requests without it get `{"result": false, "reason": "unauthorized"}`.

### ping
```json
{"action": "ping"}
→ {"result": true, "version": "2.0", "pipeline": "yunet+sface", "ready": true}
```

### authenticate_face
```json
{"action": "authenticate_face", "user_id": "alice"}
→ {"result": true, "similarity": 0.81, "reason": "match", "message": "Face recognized", "frames": 3, "threshold": 0.4}
```
The service watches the camera for the configured window (6 s by default) and answers as soon as it is sure. `reason` is one of `match`, `mismatch`, `no_face`, `low_quality`, `liveness_failed`, `locked`, `not_enrolled`, `re_enroll_required`, `camera_unavailable`.

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
