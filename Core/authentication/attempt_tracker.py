"""Per-user authentication attempt tracking and lockout enforcement."""

import time
from typing import Dict


class AttemptRecord:
    """Tracks failure count and lockout state for a single user."""

    def __init__(self):
        self.failed_count: int = 0
        self.locked_until: float = 0.0

    def reset(self) -> None:
        """Clear failure count after successful auth."""
        self.failed_count = 0
        self.locked_until = 0.0


class AttemptTracker:
    """Enforces per-user lockout after exceeding max failed attempts."""

    def __init__(self, max_attempts: int = 3, lockout_seconds: int = 300):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._records: Dict[str, AttemptRecord] = {}

    def _get_record(self, user_id: str) -> AttemptRecord:
        if user_id not in self._records:
            self._records[user_id] = AttemptRecord()
        return self._records[user_id]

    def is_locked(self, user_id: str) -> bool:
        """Check if user is currently locked out."""
        record = self._get_record(user_id)
        if record.locked_until > 0 and time.time() < record.locked_until:
            return True
        if record.locked_until > 0 and time.time() >= record.locked_until:
            record.reset()
        return False

    def record_failure(self, user_id: str) -> bool:
        """Record a failed attempt. Returns True if user is now locked out."""
        record = self._get_record(user_id)
        record.failed_count += 1
        if record.failed_count >= self.max_attempts:
            record.locked_until = time.time() + self.lockout_seconds
            return True
        return False

    def record_success(self, user_id: str) -> None:
        """Reset attempt counter after successful authentication."""
        self._get_record(user_id).reset()

    def get_remaining_attempts(self, user_id: str) -> int:
        """Return how many attempts remain before lockout."""
        record = self._get_record(user_id)
        return max(0, self.max_attempts - record.failed_count)
