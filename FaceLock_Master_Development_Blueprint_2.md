
# FaceLock - Master Development Blueprint

> **Mission:** Build FaceLock as a professional, cross-platform biometric authentication platform.

## Technology Stack

| Layer | Technology |
|---|---|
| AI & Backend | Python |
| Desktop UI | **QML (Qt Quick)** |
| Bridge | PySide6 |
| Face Recognition | InsightFace |
| Face Detection | RetinaFace / SCRFD |
| Runtime | ONNX Runtime |
| Database | SQLite |
| Encryption | cryptography |

## Architecture

```text
QML Frontend
(Dashboard, Settings, Enrollment, Logs)
        │
  PySide6 Bridge
        │
Python Backend
(Authentication, Recognition, Liveness,
Encryption, Storage, Services)
        │
Linux / Windows
```

## UI Philosophy

### QML
- Dashboard
- Enrollment
- Settings
- Logs
- Themes
- Animations
- Components

### Python
- Face Detection
- Face Recognition
- Liveness
- Authentication
- Encryption
- Storage
- Background Service
- SDK
- OS Integration

**Rule:** QML is presentation only. Authentication logic always remains in Python.

## Dashboard Structure

```text
Dashboard/
├── qml/
│   ├── pages/
│   ├── components/
│   ├── themes/
│   ├── animations/
│   └── Main.qml
├── backend/
│   └── bridge.py
├── assets/
└── main.py
```

## Development Principles

1. Architecture first.
2. Documentation first.
3. UI in QML.
4. Logic in Python.
5. Platform code stays isolated.
6. Password fallback always exists.
7. Local-first biometric processing.

## Phase Roadmap

- Phase 1 — Core AI Engine
- Phase 2 — Security & Liveness
- Phase 3 — QML Desktop Dashboard
- Phase 4 — Linux PAM + Windows Authentication
- Phase 5 — Application Lock
- Phase 6 — Python SDK
- Phase 7 — Website & Distribution
