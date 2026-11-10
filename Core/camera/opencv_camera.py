"""OpenCV implementation of video frame acquisition."""

import os
from typing import Optional, Tuple
import cv2
import numpy as np

from Core.camera.camera_interface import ICamera
from Core.config.settings import CameraSettings


class OpenCVCamera(ICamera):
    """Acquires video frames using OpenCV Videocapture."""

    def __init__(self, settings: Optional[CameraSettings] = None):
        self.settings = settings or CameraSettings()
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        """Initialize camera hardware."""
        if self.is_opened():
            return True
        self.cap = cv2.VideoCapture(self.settings.device_id, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(self.settings.device_id)
        if not self.cap.isOpened():
            return False

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.settings.fps)
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture single frame."""
        if not self.is_opened():
            return False, None
        ret, frame = self.cap.read()
        return ret, frame if ret else None

    def is_opened(self) -> bool:
        """Check status of video capture object."""
        return self.cap is not None and self.cap.isOpened()

    def release(self) -> None:
        """Close capture device."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
