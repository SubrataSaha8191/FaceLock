"""Structured audit logger for security event tracking."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_audit_counter = 0


class AuditLogger:
    """Writes structured JSON audit events to a dedicated log file."""

    def __init__(self, log_path: Path):
        global _audit_counter
        _audit_counter += 1
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # Use unique logger name to avoid handler conflicts across instances
        self._logger = logging.getLogger(f"FaceLock.Audit.{_audit_counter}")
        self._logger.propagate = False
        self._logger.handlers.clear()
        handler = logging.FileHandler(self.log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write a single structured audit event."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "user_id": user_id,
            "success": success,
            "details": details or {},
        }
        self._logger.info(json.dumps(record, default=str))

    def log_enrollment(self, user_id: str, success: bool) -> None:
        """Record an enrollment event."""
        self.log_event("ENROLLMENT", user_id=user_id, success=success)

    def log_auth_attempt(self, user_id: str, success: bool, similarity: float = 0.0) -> None:
        """Record an authentication attempt."""
        self.log_event("AUTH_ATTEMPT", user_id=user_id, success=success,
                       details={"similarity": round(similarity, 4)})

    def log_lockout(self, user_id: str) -> None:
        """Record a user lockout event."""
        self.log_event("LOCKOUT", user_id=user_id, success=False)

    def log_liveness_check(self, user_id: str, is_live: bool, confidence: float) -> None:
        """Record a liveness detection result."""
        self.log_event("LIVENESS_CHECK", user_id=user_id, success=is_live,
                       details={"confidence": round(confidence, 4)})

    def log_password_fallback(self, user_id: str, success: bool) -> None:
        """Record a password fallback attempt."""
        self.log_event("PASSWORD_FALLBACK", user_id=user_id, success=success)
