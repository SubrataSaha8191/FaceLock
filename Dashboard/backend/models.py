"""Qt Data models and helper structures for Dashboard bridge."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class UserViewModel:
    """User item presentation model for QML views."""

    user_id: str
    username: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to QML-compatible dictionary."""
        return {
            "userId": self.user_id,
            "username": self.username,
        }


@dataclass
class SystemMetricsViewModel:
    """System metrics presentation model for QML cards."""

    registered_users_count: int
    camera_active: bool
    liveness_enabled: bool
    matching_threshold: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to QML-compatible dictionary."""
        return {
            "registeredUsersCount": self.registered_users_count,
            "cameraActive": self.camera_active,
            "livenessEnabled": self.liveness_enabled,
            "matchingThreshold": self.matching_threshold,
        }
