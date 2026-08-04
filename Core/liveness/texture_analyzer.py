"""Texture-based liveness detection using Local Binary Pattern variance."""

from typing import Tuple
import cv2
import numpy as np

from Core.liveness.liveness_interface import ILivenessDetector
from Core.liveness.liveness_result import LivenessResult


class TextureAnalyzer(ILivenessDetector):
    """Detects spoofing by analyzing LBP texture variance of face region.

    Live faces exhibit richer micro-texture variance than printed photos
    or screen replays, which appear smoother after reproduction.
    """

    def __init__(self, variance_threshold: float = 15.0):
        self.variance_threshold = variance_threshold

    def check_liveness(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> LivenessResult:
        """Compute LBP variance on face crop and compare to threshold."""
        x, y, w, h = bbox
        img_h, img_w = frame.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)

        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0:
            return LivenessResult(is_live=False, confidence=0.0, method="texture_lbp")

        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        lbp_map = self._compute_lbp(gray)
        variance = float(np.var(lbp_map))

        # Normalize confidence: higher variance = more likely live
        confidence = min(variance / (self.variance_threshold * 2), 1.0)
        is_live = variance >= self.variance_threshold
        return LivenessResult(is_live=is_live, confidence=confidence, method="texture_lbp")

    @staticmethod
    def _compute_lbp(gray: np.ndarray) -> np.ndarray:
        """Compute simplified 8-neighbor LBP on grayscale image."""
        padded = cv2.copyMakeBorder(gray, 1, 1, 1, 1, cv2.BORDER_REFLECT)
        rows, cols = gray.shape
        lbp = np.zeros_like(gray, dtype=np.uint8)
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
        for bit, (dy, dx) in enumerate(offsets):
            neighbor = padded[1 + dy: 1 + dy + rows, 1 + dx: 1 + dx + cols]
            lbp |= ((neighbor >= padded[1:1 + rows, 1:1 + cols]).astype(np.uint8) << bit)
        return lbp
