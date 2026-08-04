"""Abstract liveness detector interface."""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from Core.liveness.liveness_result import LivenessResult


class ILivenessDetector(ABC):
    """Abstract interface for anti-spoofing liveness detection."""

    @abstractmethod
    def check_liveness(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> LivenessResult:
        """Analyze frame for signs of a live face within bounding box."""
        pass
