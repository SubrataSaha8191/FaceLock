"""Abstract camera capture interface."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class ICamera(ABC):
    """Abstract interface for video frame acquisition."""

    @abstractmethod
    def open(self) -> bool:
        """Open capture device."""
        pass

    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read latest frame from video device."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Release video device resources."""
        pass

    @abstractmethod
    def is_opened(self) -> bool:
        """Check if device is active."""
        pass
