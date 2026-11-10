"""Head-pose estimation from the five YuNet facial landmarks."""

from typing import Optional, Tuple

import cv2
import numpy as np

# Generic 3D face model (millimetres) in camera axes: x right, y down, z away
# from the camera. Order matches YuNet: right eye, left eye, nose, right mouth,
# left mouth. The nose tip is the origin and sits ~30 mm in front of the eyes.
_MODEL_POINTS = np.array(
    [
        [-32.0, -38.0, 30.0],
        [32.0, -38.0, 30.0],
        [0.0, 0.0, 0.0],
        [-25.0, 35.0, 24.0],
        [25.0, 35.0, 24.0],
    ],
    dtype=np.float64,
)


def estimate_pose(
    landmarks: np.ndarray, frame_size: Tuple[int, int]
) -> Optional[Tuple[float, float, float]]:
    """Return ``(yaw, pitch, roll)`` in degrees, or None if it cannot be solved.

    ``frame_size`` is ``(width, height)``. Conventions are documented on
    :class:`Core.detection.face.Face`.
    """
    if landmarks is None or landmarks.shape != (5, 2):
        return None
    w, h = frame_size
    focal = float(max(w, h))
    cam = np.array([[focal, 0, w / 2.0], [0, focal, h / 2.0], [0, 0, 1]], dtype=np.float64)
    pts = landmarks.astype(np.float64)

    # Start in front of the camera, sized so the model's eye span matches the image.
    eye_px = max(1.0, float(np.linalg.norm(pts[0] - pts[1])))
    z0 = focal * 64.0 / eye_px
    cx, cy = pts[2]
    rvec0 = np.zeros((3, 1))
    tvec0 = np.array([[(cx - w / 2.0) * z0 / focal], [(cy - h / 2.0) * z0 / focal], [z0]])
    try:
        ok, rvec, tvec = cv2.solvePnP(
            _MODEL_POINTS, pts, cam, None, rvec0, tvec0, True, cv2.SOLVEPNP_ITERATIVE
        )
    except cv2.error:
        return None
    if not ok or tvec[2, 0] <= 0:
        return None

    rot, _ = cv2.Rodrigues(rvec)
    # Rotation = Rz(roll) * Ry(yaw) * Rx(pitch) in camera axes (y down).
    sy = float(np.hypot(rot[0, 0], rot[1, 0]))
    pitch_c = float(np.degrees(np.arctan2(rot[2, 1], rot[2, 2])))
    yaw_c = float(np.degrees(np.arctan2(-rot[2, 0], sy)))
    roll_c = float(np.degrees(np.arctan2(rot[1, 0], rot[0, 0])))

    # Camera axes -> documented conventions (see Face docstring). A positive
    # rotation about +y moves the nose toward -x for this model, so flip yaw.
    # The model's +pitch drops the nose toward the mouth (looking down), so flip it.
    yaw = -yaw_c
    pitch = -_wrap(pitch_c)
    roll = roll_c
    return yaw, pitch, roll


def _wrap(angle: float) -> float:
    """Wrap an angle to [-90, 90] (PnP can return the flipped solution near +/-180)."""
    while angle > 90:
        angle -= 180
    while angle < -90:
        angle += 180
    return angle
