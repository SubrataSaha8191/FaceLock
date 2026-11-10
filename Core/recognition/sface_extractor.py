"""SFace deep face-embedding extractor (128-d, landmark-aligned)."""

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from Core.detection.face import Face
from Core.models import model_path
from Core.recognition.recognizer_interface import IFeatureExtractor

EMBEDDING_DIM = 128


class SFaceExtractor(IFeatureExtractor):
    """Aligns a face with its five landmarks and returns a unit-norm 128-d embedding.

    Each embedding averages the aligned crop and its mirror image (flip
    test-time augmentation), which makes matching noticeably steadier for
    off-axis poses.
    """

    def __init__(self, model: Optional[Path] = None, flip_augment: bool = True):
        self._rec = cv2.FaceRecognizerSF.create(str(model or model_path("sface")), "")
        self._flip = flip_augment

    def extract_from_face(self, frame: np.ndarray, face: Face) -> np.ndarray:
        if frame is None or face is None or face.row is None:
            return np.zeros(EMBEDDING_DIM, dtype=np.float32)
        aligned = self._rec.alignCrop(frame, face.row)
        feat = self._rec.feature(aligned).reshape(-1).astype(np.float64)
        if self._flip:
            feat = feat / max(np.linalg.norm(feat), 1e-9)
            flipped = self._rec.feature(cv2.flip(aligned, 1)).reshape(-1).astype(np.float64)
            feat = feat + flipped / max(np.linalg.norm(flipped), 1e-9)
        norm = np.linalg.norm(feat)
        if norm <= 0:
            return np.zeros(EMBEDDING_DIM, dtype=np.float32)
        return (feat / norm).astype(np.float32)

    def extract_embedding(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        raise NotImplementedError(
            "SFaceExtractor needs facial landmarks; use extract_from_face() with a YuNet Face."
        )
