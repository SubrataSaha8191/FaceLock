"""Abstract feature extractor interface."""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class IFeatureExtractor(ABC):
    """Abstract interface for extracting embedding vectors from face crops."""

    @abstractmethod
    def extract_embedding(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract a 1D normalized float32 embedding vector for the bounding box."""
        pass
