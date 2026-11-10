"""Abstract face detector interface."""

from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

from Core.detection.face import Face


class IFaceDetector(ABC):
    """Abstract interface for face bounding box detection."""

    @abstractmethod
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect face bounding boxes: list of (x, y, width, height)."""
        pass

    def detect(self, frame: np.ndarray) -> List[Face]:
        """Detect faces with landmarks/pose where supported, largest first.

        The default wraps :meth:`detect_faces`, so simple detectors keep working.
        """
        return sorted(
            (Face.from_bbox(b) for b in self.detect_faces(frame)),
            key=lambda f: f.area,
            reverse=True,
        )
