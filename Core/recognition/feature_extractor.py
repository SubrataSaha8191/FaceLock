"""Feature extractor implementation generating normalized embedding vectors."""

from typing import Tuple
import cv2
import numpy as np

from Core.recognition.recognizer_interface import IFeatureExtractor


class FeatureExtractor(IFeatureExtractor):
    """Generates 128-dimensional normalized feature embeddings from face crops."""

    def __init__(self, target_size: Tuple[int, int] = (128, 128)):
        self.target_size = target_size

    def extract_embedding(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Crop, resize, grayscale normalize, and extract unit-normalized feature vector."""
        x, y, w, h = bbox
        if frame is None or w <= 0 or h <= 0:
            return np.zeros(128, dtype=np.float32)

        # Clamp boundaries
        img_h, img_w = frame.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)

        face_roi = frame[y1:y2, x1:x2]
        if face_roi.size == 0:
            return np.zeros(128, dtype=np.float32)

        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, self.target_size)
        equalized = cv2.equalizeHist(resized)

        # Spatial grid downsampling to produce 128-dimensional vector
        resized_vector = cv2.resize(equalized, (16, 8)).flatten().astype(np.float32)
        norm = np.linalg.norm(resized_vector)
        if norm > 0:
            resized_vector /= norm
        return resized_vector
