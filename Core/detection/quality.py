"""Frame/face quality gating with human-readable guidance."""

from dataclasses import dataclass, field
from typing import List

import cv2
import numpy as np

from Core.detection.face import Face


@dataclass
class QualityReport:
    ok: bool
    score: float
    hint: str = ""
    reasons: List[str] = field(default_factory=list)


def assess_face(
    frame: np.ndarray,
    face: Face,
    min_face_px: int = 80,
    min_det_score: float = 0.75,
    min_sharpness: float = 12.0,
) -> QualityReport:
    """Check that a face is big, bright, sharp and fully inside the frame."""
    h, w = frame.shape[:2]
    x, y, bw, bh = face.bbox
    reasons: List[str] = []

    if face.score < min_det_score:
        reasons.append("unclear")
    if bw < min_face_px:
        reasons.append("too_far")
    margin = 0.02
    if x < -margin * w or y < -margin * h or x + bw > (1 + margin) * w or y + bh > (1 + margin) * h:
        reasons.append("cut_off")

    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(w, x + bw), min(h, y + bh)
    roi = frame[y1:y2, x1:x2]
    sharp = 0.0
    if roi.size == 0:
        reasons.append("cut_off")
        luma = 0.0
    else:
        gray = cv2.cvtColor(cv2.resize(roi, (112, 112)), cv2.COLOR_BGR2GRAY)
        luma = float(gray.mean())
        sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if luma < 35:
            reasons.append("too_dark")
        elif luma > 225:
            reasons.append("too_bright")
        if sharp < min_sharpness:
            reasons.append("blurry")

    hints = {
        "too_far": "Move a little closer",
        "cut_off": "Keep your whole face in view",
        "too_dark": "Needs more light on your face",
        "too_bright": "Too bright, reduce glare",
        "blurry": "Hold still for a moment",
        "unclear": "Face the camera",
    }
    order = ["cut_off", "too_far", "too_dark", "too_bright", "unclear", "blurry"]
    hint = next((hints[r] for r in order if r in reasons), "")
    score = float(
        np.clip(face.score, 0, 1) * min(1.0, bw / (min_face_px * 1.5)) * min(1.0, (sharp + 1) / 40.0)
    )
    return QualityReport(ok=not reasons, score=score, hint=hint, reasons=reasons)
