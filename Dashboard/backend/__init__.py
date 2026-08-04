"""Dashboard backend bridge package."""

from Dashboard.backend.bridge import FaceLockBridge
from Dashboard.backend.camera_provider import LiveCameraProvider

__all__ = ["FaceLockBridge", "LiveCameraProvider"]
