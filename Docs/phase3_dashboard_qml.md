# Phase 3: QML Desktop Dashboard Specification

## Overview
Phase 3 delivers the cross-platform Qt Quick (QML) desktop user interface for FaceLock, powered by PySide6 bridge bindings.

## Architecture

```text
+-----------------------------------------------------------+
|                     QML Frontend Layer                    |
|  (Main.qml, DashboardPage, EnrollmentPage, SettingsPage)  |
+-----------------------------+-----------------------------+
                              | QML Signals & Properties
                              v
+-----------------------------------------------------------+
|                   PySide6 Bridge Layer                    |
|   (FaceLockBridge QObject, LiveCameraProvider ImageProv)  |
+-----------------------------+-----------------------------+
                              | Python Calls
                              v
+-----------------------------------------------------------+
|                    Core Python Engine                     |
|  (AuthenticationEngine, Storage, Encryption, Perception)  |
+-----------------------------------------------------------+
```

## Key Components

1. **`Dashboard/backend/bridge.py` (`FaceLockBridge`)**:
   - Registered as `facelockBridge` context property in QML.
   - Exposes `@Slot()` methods: `enrollUser()`, `verifyUser()`, `getUsers()`, `deleteUser()`, `getAuditLogs()`, `getSettings()`, `updateSettings()`, `toggleCamera()`.
   - Emits signals: `statusMessageChanged`, `userListChanged`, `metricsUpdated`, `cameraFrameReady`.

2. **`Dashboard/backend/camera_provider.py` (`LiveCameraProvider`)**:
   - Inherits `QQuickImageProvider` with image type `QQuickImageProvider.ImageType.Image`.
   - Streams BGR frames captured from `OpenCVCamera` converted directly to `QImage(Format_RGB888)`.
   - Referenced in QML as `source: "image://livecamera/frame?" + Math.random()`.

3. **`Dashboard/qml/` Layout**:
   - `themes/Theme.qml`: Global dark UI theme color tokens and font sizes.
   - `components/`: Modular widgets (`MetricCard`, `StatusBadge`, `PrimaryButton`, `UserCard`, `NavigationBar`).
   - `pages/`: Page views (`DashboardPage`, `EnrollmentPage`, `CameraPreviewPage`, `SettingsPage`, `LogsPage`).
   - `Main.qml`: Root ApplicationWindow with sidebar navigation and StackView page container.
