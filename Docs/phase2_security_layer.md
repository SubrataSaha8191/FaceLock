# Phase 2: Security Layer Specification

## Overview
Phase 2 hardens FaceLock with anti-spoofing liveness detection, adaptive risk-based thresholds,
per-user lockout enforcement, structured audit logging, and password fallback authentication.

## Components

### 1. Liveness Detection (`Core/liveness/`)
- **TextureAnalyzer**: LBP variance analysis detects printed photos and screen replays.
- **BlinkDetector**: Eye Aspect Ratio estimation confirms open vs. closed eyes.
- **CompositeLiveness**: Weighted combination of multiple sub-detectors.

### 2. Audit Logging (`Core/utils/audit_logger.py`)
- Structured JSON events written to `~/.facelock/audit.log`.
- Events: ENROLLMENT, AUTH_ATTEMPT, LOCKOUT, LIVENESS_CHECK, PASSWORD_FALLBACK.

### 3. Attempt Tracking (`Core/authentication/attempt_tracker.py`)
- Per-user failure counter with configurable max attempts.
- Automatic lockout with time-based cooldown expiry.

### 4. Risk Evaluator (`Core/authentication/risk_evaluator.py`)
- Computes risk score from: failure history, liveness confidence, time-of-day.
- Elevates matching threshold proportionally to risk (base 0.6 → max 0.85).

### 5. Password Fallback (`Core/authentication/password_fallback.py`)
- PBKDF2-HMAC-SHA256 salted password hashing.
- Triggered when face authentication is unavailable or exhausts max attempts.

## Authentication Flow

```text
[ Frame ] --> [ Lockout Check ] --> [ Liveness ] --> [ Risk Threshold ]
                   |                    |                    |
                LOCKED              SPOOF DETECTED       ADJUSTED
                   |                    |                    |
                   v                    v                    v
              [ Password          [ Record Fail ]    [ Vector Match ]
                Fallback ]              |                    |
                                        v                    v
                                   [ Lockout? ]       [ PASS / FAIL ]
                                                          |
                                                    [ Audit Log ]
```
