"""OpenCV Haar Cascade Face Detector implementation."""

from typing import List, Optional, Tuple
import cv2
import numpy as np

from Core.detection.detector_interface import IFaceDetector


class CascadeDetector(IFaceDetector):
    """Detects faces in BGR image frames using Haar Cascades."""

    def __init__(self, cascade_path: Optional[str] = None):
        if cascade_path is None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Find face bounding boxes inside the frame."""
        if frame is None or frame.size == 0:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
        )

        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
