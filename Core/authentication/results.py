"""Result and progress types for the authentication pipeline."""

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from Core.detection.face import Face

REASON_MESSAGES = {
    "match": "Face recognized",
    "locked": "Too many failed attempts. Try again later or use your password",
    "not_enrolled": "No face profile enrolled for this user",
    "re_enroll_required": "Face profile is from an older version. Please enroll again",
    "no_face": "No face found. Look at the camera",
    "low_quality": "Couldn't get a clear view. Check lighting and distance",
    "liveness_failed": "Liveness check failed",
    "mismatch": "Face didn't match",
    "camera_unavailable": "Camera unavailable",
}


@dataclass
class AuthResult:
    """Final outcome of an authentication attempt."""

    ok: bool
    score: float = 0.0
    reason: str = "mismatch"
    threshold: float = 0.0
    frames: int = 0
    matches: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            self.message = REASON_MESSAGES.get(self.reason, self.reason)


@dataclass
class AuthProgress:
    """One step of a streaming authentication attempt (for live UIs)."""

    hint: str = ""
    score: float = 0.0
    matches: int = 0
    frames: int = 0
    face: Optional[Face] = None
    frame: Optional[np.ndarray] = field(default=None, repr=False)
    done: bool = False
    result: Optional[AuthResult] = None
