"""Abstract face detector interface."""

from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np


class IFaceDetector(ABC):
    """Abstract interface for face bounding box detection."""

    @abstractmethod
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect face bounding boxes: list of (x, y, width, height)."""
        pass
