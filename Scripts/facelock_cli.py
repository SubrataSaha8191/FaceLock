"""Command Line Interface (CLI) for FaceLock administration."""

import argparse
import sys
import cv2

from Core.config.settings import SystemSettings
from Core.camera.opencv_camera import OpenCVCamera
from Core.detection.cascade_detector import CascadeDetector
from Core.recognition.feature_extractor import FeatureExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine


def setup_engine(settings: SystemSettings) -> AuthenticationEngine:
    """Initialize system components."""
    detector = CascadeDetector()
    extractor = FeatureExtractor()
    storage = EncryptedSQLiteStorage(settings.db_path)
    return AuthenticationEngine(settings, detector, extractor, storage)


def cmd_test_camera(settings: SystemSettings) -> None:
    """Test webcam capture and face detection."""
    camera = OpenCVCamera(settings.camera)
    detector = CascadeDetector()
    if not camera.open():
        print("Error: Unable to access camera.")
        return

    print("Camera active. Press 'q' to exit test window.")
    while True:
        ret, frame = camera.read_frame()
        if not ret or frame is None:
            break
        faces = detector.detect_faces(frame)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow("FaceLock Camera Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="FaceLock Biometric CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("test-camera", help="Test camera video capture")
    
    enroll_p = subparsers.add_parser("enroll", help="Enroll a new user")
    enroll_p.add_argument("--id", required=True, help="User ID")
    enroll_p.add_argument("--name", required=True, help="Username")
    enroll_p.add_argument("--secret", required=True, help="Master secret/passphrase")

    verify_p = subparsers.add_parser("verify", help="Authenticate user")
    verify_p.add_argument("--id", required=True, help="User ID")
    verify_p.add_argument("--secret", required=True, help="Master secret/passphrase")

    args = parser.parse_args()
    settings = SystemSettings()

    if args.command == "test-camera":
        cmd_test_camera(settings)
    elif args.command == "enroll":
        engine = setup_engine(settings)
        camera = OpenCVCamera(settings.camera)
        if camera.open():
            print("Look into camera for enrollment...")
            for _ in range(10):  # Warmup
                camera.read_frame()
            ret, frame = camera.read_frame()
            camera.release()
            if ret and frame is not None:
                ok = engine.enroll_user(args.id, args.name, args.secret, frame)
                print("Enrollment successful!" if ok else "Enrollment failed.")
    elif args.command == "verify":
        engine = setup_engine(settings)
        camera = OpenCVCamera(settings.camera)
        if camera.open():
            print("Look into camera for verification...")
            for _ in range(10):
                camera.read_frame()
            ret, frame = camera.read_frame()
            camera.release()
            if ret and frame is not None:
                passed, score = engine.authenticate_user(args.id, args.secret, frame)
                print(f"Auth result: {'PASSED' if passed else 'FAILED'} (Score: {score:.4f})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
