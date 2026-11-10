"""Command Line Interface (CLI) for FaceLock administration."""

import argparse
import sys
import cv2

from Core.config.settings import SystemSettings
from Core.camera.opencv_camera import OpenCVCamera
from Core.camera.stream import CameraStream
from Core.detection.yunet_detector import YuNetDetector
from Core.enrollment import EnrollmentSession
from Core.recognition.sface_extractor import SFaceExtractor
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage
from Core.authentication.auth_engine import AuthenticationEngine


def setup_engine(settings: SystemSettings) -> AuthenticationEngine:
    """Initialize system components."""
    detector = YuNetDetector(score_threshold=settings.security.detector_score_threshold)
    extractor = SFaceExtractor()
    storage = EncryptedSQLiteStorage(settings.db_path)
    return AuthenticationEngine(settings, detector, extractor, storage)


def cmd_test_camera(settings: SystemSettings) -> None:
    """Test webcam capture and face detection."""
    camera = OpenCVCamera(settings.camera)
    detector = YuNetDetector()
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
        session = EnrollmentSession(engine.detector, engine.extractor)
        with CameraStream(settings.camera) as stream:
            if stream.cap is None:
                print("Error: Unable to access camera.")
                return
            print("Look at the camera, then slowly move your head in a circle.")
            last_hint = ""
            for frame in stream.frames(timeout=120):
                st = session.process(frame)
                if st.hint != last_hint:
                    print(f"  [{int(st.progress * 100):3d}%] {st.hint}")
                    last_hint = st.hint
                if session.complete:
                    break
        if session.can_finish:
            ok = engine.enroll_template(args.id, args.name, args.secret, session.build_template())
            print("Enrollment successful!" if ok else "Enrollment failed.")
        else:
            print("Enrollment incomplete: not enough angles captured.")
    elif args.command == "verify":
        engine = setup_engine(settings)
        timeout = settings.security.auth_timeout_seconds
        with CameraStream(settings.camera) as stream:
            if stream.cap is None:
                print("Error: Unable to access camera.")
                return
            print("Look into the camera for verification...")
            res = engine.authenticate_frames(args.id, args.secret, stream.frames(timeout), timeout)
        print(f"Auth result: {'PASSED' if res.ok else 'FAILED'} "
              f"(Score: {res.score:.4f}, {res.message})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
