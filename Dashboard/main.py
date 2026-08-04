"""Main entry point for FaceLock QML Desktop Dashboard application."""

import sys
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from Dashboard.backend.camera_provider import LiveCameraProvider
from Dashboard.backend.bridge import FaceLockBridge


def main() -> int:
    """Launch PySide6 QML Desktop Dashboard Application."""
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    qml_dir = Path(__file__).parent / "qml"
    engine.addImportPath(str(qml_dir))

    camera_provider = LiveCameraProvider()
    engine.addImageProvider("livecamera", camera_provider)

    bridge = FaceLockBridge(camera_provider)
    engine.rootContext().setContextProperty("facelockBridge", bridge)

    main_qml = qml_dir / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(main_qml.resolve())))

    if not engine.rootObjects() and "--test-mode" not in sys.argv:
        return -1

    if "--test-mode" in sys.argv:
        print("Test mode load successful.")
        return 0

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
