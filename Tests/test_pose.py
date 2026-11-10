"""Head-pose estimation: recovers known angles and keeps the documented sign conventions."""

import numpy as np
import pytest

from Core.detection.pose import _MODEL_POINTS, estimate_pose

W, H, F = 640, 480, 640.0
CAM = np.array([[F, 0, W / 2], [0, F, H / 2], [0, 0, 1.0]])


def _project(model_yaw, model_pitch, model_roll, z=500.0):
    a, b, c = np.radians([model_yaw, model_pitch, model_roll])
    ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    pts = (rz @ ry @ rx @ _MODEL_POINTS.T).T + np.array([0, 0, z])
    uv = (CAM @ pts.T).T
    return (uv[:, :2] / uv[:, 2:3]).astype(np.float32)


def test_frontal_face_is_zero():
    yaw, pitch, roll = estimate_pose(_project(0, 0, 0), (W, H))
    assert abs(yaw) < 1 and abs(pitch) < 1 and abs(roll) < 1


@pytest.mark.parametrize("angle", [10, 25, 45, 60])
def test_yaw_magnitude_recovered_and_sign_follows_nose(angle):
    for sign in (1, -1):
        lm = _project(sign * angle, 0, 0)
        yaw, _, _ = estimate_pose(lm, (W, H))
        nose_dx = lm[2, 0] - (lm[0, 0] + lm[1, 0]) / 2
        assert abs(abs(yaw) - angle) < 2
        # yaw > 0 <=> nose displaced toward image right
        assert (yaw > 0) == (nose_dx > 0)


def test_pitch_sign_up_is_positive():
    neutral = _project(0, 0, 0)
    for model_pitch in (15, -15):
        lm = _project(0, model_pitch, 0)
        _, pitch, _ = estimate_pose(lm, (W, H))
        gap = lm[2, 1] - (lm[0, 1] + lm[1, 1]) / 2
        neutral_gap = neutral[2, 1] - (neutral[0, 1] + neutral[1, 1]) / 2
        # Nose farther below the eyes than neutral => face looking down => pitch < 0
        assert (pitch < 0) == (gap > neutral_gap)
        assert abs(abs(pitch) - 15) < 2


def test_roll_clockwise_positive():
    _, _, roll = estimate_pose(_project(0, 0, 15), (W, H))
    assert 13 < roll < 17


def test_invalid_landmarks():
    assert estimate_pose(None, (W, H)) is None
    assert estimate_pose(np.zeros((3, 2), np.float32), (W, H)) is None
