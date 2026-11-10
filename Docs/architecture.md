# FaceLock Architecture Overview

## Design Principles

1. **Architecture First**: Components partitioned into `Core/`, `Dashboard/`, `Service/`, `Linux/`, `Windows/`, and `SDK/`.
2. **Platform Separation**: OS-agnostic logic lives in `Core/`. OS-specific integrations reside in their respective directories.
3. **UI in QML / Logic in Python**: QML is presentation only. Authentication logic always remains in Python.
4. **Privacy First**: Raw biometric images are never persisted. All vector embeddings are encrypted using AES-GCM.
5. **Clean Code & Line Limits**: Source code files (Python & QML) are strictly limited to **≤ 150 lines of code**.

## Full System Diagram

```text
 ┌────────────────────────────────────────────────────────────┐
 │                     QML Desktop Dashboard                  │
 │  (Main.qml, DashboardPage, EnrollmentPage, SettingsPage)   │
 └─────────────────────────┬──────────────────────────────────┘
                           │ QML Signals & Slots
                           ▼
 ┌────────────────────────────────────────────────────────────┐
 │                    PySide6 Bridge Layer                     │
 │       (FaceLockBridge QObject, LiveCameraProvider)          │
 └─────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
 ┌────────────────────────────────────────────────────────────┐
 │                Core Authentication Engine                   │
 │  (Liveness, AttemptTracker, RiskEval, PasswordFallback)     │
 └───────┬─────────────────┬──────────────────┬───────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
 ┌───────────────┐ ┌───────────────┐ ┌────────────────────┐
 │ Perception    │ │ Security      │ │ Storage & Crypto   │
 │ (Detect/Rec)  │ │ (Audit/Lock)  │ │ (SQLite/AES-GCM)   │
 └───────────────┘ └───────────────┘ └────────────────────┘

                    OS INTEGRATION LAYER
 ┌────────────────────────────────────────────────────────────┐
 │        Background Auth Service (local socket / loopback)     │
 │                 Service/auth/auth_service.py                │
 └───────┬────────────────────────────────────┬───────────────┘
         │                                    │
         ▼                                    ▼
 ┌───────────────────┐            ┌───────────────────────┐
 │ Linux PAM Module  │            │ Windows Cred Provider │
 │ (pam_facelock.py) │            │ (credential_bridge.py)│
 └───────────────────┘            └───────────────────────┘
```

## Security Model

- **Key Derivation**: PBKDF2 with HMAC-SHA256 (100,000+ iterations)
- **Symmetric Cipher**: AES-256-GCM authenticated encryption
- **Zero-Storage Policy**: Transient frames in memory only
- **Liveness Detection**: Composite LBP texture + Eye Aspect Ratio blink
- **Adaptive Security**: Risk-scored dynamic threshold elevation
- **Lockout Policy**: Per-user lockout with automatic cooldown
- **Password Fallback**: PBKDF2-hashed password for fallback auth
- **Audit Trail**: Structured JSON log for all security events
- **OS Integration**: local service for PAM and the Credential Provider bridge. Linux uses a UNIX socket; Windows (which has no `AF_UNIX` in Python) uses loopback TCP with a per-user secret token published in `endpoint.json`
