"""Camera capture package for FaceLock."""

from Core.camera.camera_interface import ICamera
from Core.camera.opencv_camera import OpenCVCamera

__all__ = ["ICamera", "OpenCVCamera"]
