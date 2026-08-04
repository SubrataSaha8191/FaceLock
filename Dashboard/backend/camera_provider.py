"""PySide6 QQuickImageProvider for streaming camera frames to QML."""

import cv2
import numpy as np
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class LiveCameraProvider(QQuickImageProvider):
    """Image provider delivering live camera frames directly to QML components."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.current_frame: QImage = self._create_placeholder_image()

    def update_frame_from_cv(self, cv_frame: np.ndarray) -> None:
        """Convert BGR numpy array frame to QImage format."""
        if cv_frame is None or cv_frame.size == 0:
            return
        rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        # Create QImage copy to ensure memory safety
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        self.current_frame = q_img

    def requestImage(self, id: str, size: QSize, requestedSize: QSize) -> QImage:
        """Return current frame image when requested by QML."""
        if size is not None and not self.current_frame.isNull():
            size.setWidth(self.current_frame.width())
            size.setHeight(self.current_frame.height())

        if requestedSize.isValid() and not requestedSize.isEmpty():
            return self.current_frame.scaled(requestedSize)

        return self.current_frame

    @staticmethod
    def _create_placeholder_image() -> QImage:
        """Create a default 640x480 dark placeholder QImage."""
        img = QImage(640, 480, QImage.Format.Format_RGB888)
        img.fill(0x1E1E2E)
        return img
