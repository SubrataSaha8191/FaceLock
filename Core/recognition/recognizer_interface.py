"""Abstract feature extractor interface."""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from Core.detection.face import Face


class IFeatureExtractor(ABC):
    """Abstract interface for extracting embedding vectors from face crops."""

    @abstractmethod
    def extract_embedding(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract a 1D normalized float32 embedding vector for the bounding box."""
        pass

    def extract_from_face(self, frame: np.ndarray, face: Face) -> np.ndarray:
        """Extract an embedding for a detected face (landmark-aware extractors override)."""
        return self.extract_embedding(frame, face.bbox)
