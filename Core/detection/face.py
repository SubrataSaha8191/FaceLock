"""Detected-face data model shared by detection, recognition and enrollment."""

from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

BBox = Tuple[int, int, int, int]


@dataclass
class Face:
    """A detected face.

    ``landmarks`` is a (5, 2) float32 array in *image* coordinates, in YuNet order:
    right eye, left eye, nose tip, right mouth corner, left mouth corner
    ("right" = the subject's right, which is the left side of an un-mirrored frame).

    ``row`` is the raw 15-value YuNet row (x, y, w, h, 5 landmarks, score) that
    ``cv2.FaceRecognizerSF.alignCrop`` consumes.

    Pose angles are in degrees, relative to a camera looking straight at the face:
    ``yaw`` > 0 means the nose points toward the image right (un-mirrored frame),
    ``pitch`` > 0 means the face looks up, ``roll`` > 0 is a clockwise head tilt.
    """

    bbox: BBox
    score: float = 1.0
    landmarks: Optional[np.ndarray] = None
    row: Optional[np.ndarray] = None
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    pose_valid: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def area(self) -> int:
        return max(0, self.bbox[2]) * max(0, self.bbox[3])

    @property
    def center(self) -> Tuple[float, float]:
        x, y, w, h = self.bbox
        return x + w / 2.0, y + h / 2.0

    @staticmethod
    def from_bbox(bbox: BBox) -> "Face":
        """Wrap a bare bounding box (used by legacy detectors and test doubles)."""
        x, y, w, h = bbox
        return Face(bbox=(int(x), int(y), int(w), int(h)))


def coerce_face(item) -> Face:
    """Accept either a Face or a legacy ``(x, y, w, h)`` tuple."""
    return item if isinstance(item, Face) else Face.from_bbox(tuple(item))
