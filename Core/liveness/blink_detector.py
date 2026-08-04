"""Blink-based liveness detection using Eye Aspect Ratio analysis."""

from typing import List, Tuple
import cv2
import numpy as np

from Core.liveness.liveness_interface import ILivenessDetector
from Core.liveness.liveness_result import LivenessResult


class BlinkDetector(ILivenessDetector):
    """Detects eye blinks via Eye Aspect Ratio (EAR) estimation.

    Uses Haar Cascade eye detector to locate eyes, then estimates EAR
    from the eye region aspect ratio. Open eyes produce higher EAR.
    """

    def __init__(self, ear_threshold: float = 0.21):
        self.ear_threshold = ear_threshold
        cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
        self.eye_cascade = cv2.CascadeClassifier(cascade_path)

    def check_liveness(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> LivenessResult:
        """Detect eyes within face ROI and estimate openness."""
        x, y, w, h = bbox
        img_h, img_w = frame.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)

        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0:
            return LivenessResult(is_live=False, confidence=0.0, method="blink_ear")

        eyes = self._detect_eyes(face_roi)
        if len(eyes) < 2:
            return LivenessResult(is_live=False, confidence=0.2, method="blink_ear")

        avg_ear = self._estimate_ear(eyes)
        is_live = avg_ear > self.ear_threshold
        confidence = min(avg_ear / (self.ear_threshold * 2), 1.0)
        return LivenessResult(is_live=is_live, confidence=confidence, method="blink_ear")

    def _detect_eyes(self, face_roi: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Find eye regions within face crop."""
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        eyes = self.eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return [(int(ex), int(ey), int(ew), int(eh)) for ex, ey, ew, eh in eyes]

    @staticmethod
    def _estimate_ear(eyes: List[Tuple[int, int, int, int]]) -> float:
        """Estimate Eye Aspect Ratio from detected eye bounding boxes."""
        ratios = []
        for _, _, ew, eh in eyes[:2]:
            if ew > 0:
                ratios.append(eh / ew)
        return sum(ratios) / len(ratios) if ratios else 0.0
