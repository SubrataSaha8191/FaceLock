"""Liveness result data model."""

from dataclasses import dataclass


@dataclass
class LivenessResult:
    """Outcome of a liveness detection check."""

    is_live: bool
    confidence: float
    method: str

    def __str__(self) -> str:
        status = "LIVE" if self.is_live else "SPOOF"
        return f"[{status}] {self.method} (confidence: {self.confidence:.3f})"
