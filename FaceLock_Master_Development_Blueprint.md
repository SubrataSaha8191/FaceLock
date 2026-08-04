
# FaceLock - Master Development Blueprint

> **Mission:** Build FaceLock as a professional, cross-platform biometric authentication platform. Every feature must follow the project architecture and folder structure.

---

# Development Principles

1. **Architecture First**
   - Decide where a feature belongs before writing code.
   - Never place random scripts or modules in the project root.

2. **Documentation First**
   - Update the relevant document in `Docs/` before implementing architectural changes.

3. **Platform Separation**
   - Platform-independent code stays in `Core/`.
   - Linux-specific code stays in `Linux/`.
   - Windows-specific code stays in `Windows/`.

4. **Privacy First**
   - Face embeddings are encrypted.
   - Raw face images are not stored after enrollment unless explicitly required.
   - Password fallback is always available.

---

# Current Folder Structure

```text
FACELOCK/
├── .github/
├── Assets/
├── Core/
│   ├── authentication/
│   ├── camera/
│   ├── config/
│   ├── detection/
│   ├── encryption/
│   ├── liveness/
│   ├── recognition/
│   ├── storage/
│   └── utils/
├── Dashboard/
│   ├── assets/
│   ├── pages/
│   ├── ui/
│   ├── widgets/
│   └── main.py
├── Docs/
├── Installer/
├── Linux/
│   ├── docs/
│   ├── installer/
│   ├── pam/
│   └── systemd/
├── Models/
│   ├── detection/
│   ├── liveness/
│   ├── recognition/
│   └── README.md
├── Plugins/
├── Scripts/
├── SDK/
│   ├── docs/
│   ├── examples/
│   ├── facelock/
│   └── tests/
├── Service/
│   ├── api/
│   ├── auth/
│   ├── daemon/
│   └── main.py
├── Tests/
├── Windows/
│   ├── credential_provider/
│   ├── docs/
│   ├── installer/
│   └── service/
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt
└── SECURITY.md
```

---

# Folder Responsibilities

| Folder | Responsibility |
|--------|----------------|
| Core | AI engine, authentication, encryption, storage |
| Dashboard | PySide6 desktop application |
| Service | Background authentication service and API |
| Linux | PAM, systemd, installers |
| Windows | Credential provider bridge and installer |
| Models | AI model files only |
| SDK | Python SDK for developers |
| Plugins | Third-party integrations |
| Scripts | Build and maintenance scripts |
| Tests | Unit and integration tests |
| Docs | Architecture and design documents |

---

# Development Workflow

```text
Feature Idea
      ↓
Identify Responsible Folder
      ↓
Update Documentation
      ↓
Create Required Files/Folders
      ↓
Implement Feature
      ↓
Write Tests
      ↓
Commit to Git
```

---

# Phase Roadmap

## Phase 1 – Core AI Engine
- Camera integration
- Face detection
- Face recognition
- Embedding generation
- Encrypted storage
- CLI prototype

## Phase 2 – Security Layer
- Liveness detection
- Authentication engine
- Logging
- Adaptive security
- Password fallback

## Phase 3 – Dashboard
- Enrollment wizard
- Settings
- Camera preview
- User management
- Security configuration

## Phase 4 – Operating System Authentication
- Linux PAM integration
- Windows credential-provider bridge
- Installer integration

## Phase 5 – Application Lock
- Lock desktop applications
- Trusted applications
- Authentication prompts

## Phase 6 – Python SDK
- `pip install facelock`
- Developer API
- Examples
- Documentation

## Phase 7 – Distribution
- Website
- Linux packages
- Windows installer
- GitHub Releases

---

# Rules for Creating Files and Folders

- Never add feature code directly to the repository root.
- Create new folders only when they have a clear responsibility.
- Add `__init__.py` for Python packages.
- Keep Core platform-independent.
- Store runtime data separately (future `Data/` directory).
- Update documentation whenever the architecture changes.

---

# Coding Session Checklist

Before writing code, answer:

- Which phase are we working on?
- Which folder is responsible?
- Which files need to be created?
- Which documentation must be updated?
- Which tests should be written?

Only then begin implementation.

---

# Long-Term Vision

FaceLock should evolve from a face recognition project into a complete biometric authentication platform featuring:

- OS authentication
- Application locking
- Python SDK
- Plugin ecosystem
- Linux and Windows support
- Website and installers
- Open-source community
- Enterprise capabilities

