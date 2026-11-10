"""Low-light and exposure helpers for webcam frames."""

import cv2
import numpy as np

_CLAHE = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))


def mean_luma(frame: np.ndarray) -> float:
    """Average luminance (0-255) of a BGR frame."""
    if frame is None or frame.size == 0:
        return 0.0
    small = frame[::8, ::8]
    return float(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).mean())


def enhance_low_light(frame: np.ndarray) -> np.ndarray:
    """Brighten and equalise a dim frame (gamma lift + CLAHE on luminance)."""
    luma = mean_luma(frame)
    out = frame
    if luma < 90:
        # Pick a gamma that pulls the mean toward ~110.
        gamma = float(np.clip(np.log(max(luma, 8.0) / 255.0) / np.log(110.0 / 255.0), 1.0, 3.0))
        lut = np.array([((i / 255.0) ** (1.0 / gamma)) * 255 for i in range(256)], dtype=np.uint8)
        out = cv2.LUT(out, lut)
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = _CLAHE.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
