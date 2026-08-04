"""Face detection package for FaceLock."""

from Core.detection.detector_interface import IFaceDetector
from Core.detection.cascade_detector import CascadeDetector

__all__ = ["IFaceDetector", "CascadeDetector"]
