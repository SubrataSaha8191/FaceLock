"""Continuous camera frame stream for unlock attempts."""

import glob
import os
import re
import time
from typing import Iterator, List, Optional

import cv2
import numpy as np

from Core.config.settings import CameraSettings
from Core.utils.logger import get_logger

logger = get_logger("CameraStream")


def _open_capture(device: int) -> "cv2.VideoCapture":
    """Open a camera; DirectShow on Windows (the default backend is slow and flaky there)."""
    if os.name == "nt":
        cap = cv2.VideoCapture(device, cv2.CAP_DSHOW)
        if cap.isOpened():
            return cap
        cap.release()
    return cv2.VideoCapture(device)


class CameraStream:
    """Opens a webcam once and yields frames until a deadline.

    Compared with grabbing a single frame after a fixed number of reads, this lets
    auto-exposure settle (dark start-up frames are skipped, not judged) and gives
    the recogniser many frames to choose from.
    """

    def __init__(self, settings: Optional[CameraSettings] = None):
        self.settings = settings or CameraSettings()
        self.cap: Optional[cv2.VideoCapture] = None
        self.device_used: Optional[int] = None

    def open(self) -> bool:
        for device in self._candidate_devices():
            cap = _open_capture(device)
            if not cap.isOpened():
                cap.release()
                continue
            # MJPG is what lets most webcams deliver 720p at 30 fps over USB 2.
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.frame_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.frame_height)
            cap.set(cv2.CAP_PROP_FPS, self.settings.fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap, self.device_used = cap, device
            return True
        logger.error("No usable camera found.")
        return False

    def _candidate_devices(self) -> List[int]:
        preferred = self.settings.device_id
        others = sorted(
            int(m.group(1))
            for p in glob.glob("/dev/video*")
            if (m := re.search(r"video(\d+)$", p)) and int(m.group(1)) != preferred
        )
        return [preferred] + others[:4]

    def frames(self, timeout: float) -> Iterator[np.ndarray]:
        """Yield BGR frames until ``timeout`` seconds have passed."""
        if self.cap is None:
            return
        start = time.monotonic()
        deadline = start + timeout
        warm = 0
        failures = 0
        while time.monotonic() < deadline:
            ok, frame = self.cap.read()
            if not ok or frame is None or frame.size == 0:
                failures += 1
                if failures > 30:
                    logger.error("Camera stopped delivering frames.")
                    return
                time.sleep(0.02)
                continue
            failures = 0
            warm += 1
            # Skip the first couple of frames and any still-black ones while the
            # sensor wakes up, but never for more than ~1.2 s.
            if time.monotonic() - start < 1.2 and (warm <= 2 or float(frame[::16, ::16].mean()) < 4):
                continue
            yield frame

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __enter__(self) -> "CameraStream":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()
