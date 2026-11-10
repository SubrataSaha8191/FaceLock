"""YuNet face detector: robust to head rotation, small faces and uneven light."""

from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

from Core.camera.enhance import enhance_low_light, mean_luma
from Core.detection.detector_interface import IFaceDetector
from Core.detection.face import Face
from Core.detection.pose import estimate_pose
from Core.models import model_path

# Longest side the network sees. Detection runs on a downscaled copy for speed;
# boxes/landmarks are mapped back so embeddings are still cropped at full resolution.
_MAX_SIDE = 640


class YuNetDetector(IFaceDetector):
    """Detects faces with landmarks and head pose using OpenCV's YuNet model."""

    def __init__(
        self,
        model: Optional[Path] = None,
        score_threshold: float = 0.7,
        nms_threshold: float = 0.3,
        top_k: int = 20,
        low_light_luma: float = 70.0,
    ):
        self._path = str(model or model_path("yunet"))
        self._score = score_threshold
        self._nms = nms_threshold
        self._top_k = top_k
        self._low_light_luma = low_light_luma
        self._det = cv2.FaceDetectorYN.create(
            self._path, "", (320, 320), score_threshold, nms_threshold, top_k
        )
        self._size = (320, 320)
        self.last_frame_used: Optional[np.ndarray] = None

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Bounding boxes only (interface compatibility)."""
        return [f.bbox for f in self.detect(frame)]

    def detect(self, frame: np.ndarray) -> List[Face]:
        """Detect faces, largest first. Retries on a light-enhanced frame when needed.

        ``last_frame_used`` holds the frame the returned faces refer to (it is an
        enhanced copy if the retry produced them); embed from that frame.
        """
        self.last_frame_used = frame
        if frame is None or frame.size == 0:
            return []

        dark = mean_luma(frame) < self._low_light_luma
        candidates = [enhance_low_light(frame)] if dark else [frame]
        if not dark:
            candidates.append(None)  # lazily enhanced second attempt

        for cand in candidates:
            if cand is None:
                cand = enhance_low_light(frame)
            faces = self._detect_once(cand)
            if faces:
                self.last_frame_used = cand
                faces.sort(key=lambda f: f.area, reverse=True)
                return faces
        return []

    def _detect_once(self, frame: np.ndarray) -> List[Face]:
        h, w = frame.shape[:2]
        scale = min(1.0, _MAX_SIDE / float(max(h, w)))
        small = frame if scale == 1.0 else cv2.resize(frame, (int(w * scale), int(h * scale)))
        sh, sw = small.shape[:2]
        if (sw, sh) != self._size:
            self._det.setInputSize((sw, sh))
            self._size = (sw, sh)
        _, rows = self._det.detect(small)
        if rows is None:
            return []

        faces: List[Face] = []
        for row in rows:
            row = row.astype(np.float32).copy()
            if scale != 1.0:
                row[:14] /= scale
            x, y, bw, bh = row[:4]
            if bw < 8 or bh < 8:
                continue
            lm = row[4:14].reshape(5, 2).copy()
            face = Face(
                bbox=(int(round(x)), int(round(y)), int(round(bw)), int(round(bh))),
                score=float(row[14]),
                landmarks=lm,
                row=row,
            )
            pose = estimate_pose(lm, (w, h))
            if pose is not None:
                face.yaw, face.pitch, face.roll = pose
                face.pose_valid = True
            faces.append(face)
        return faces
