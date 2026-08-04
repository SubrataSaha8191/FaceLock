"""Enhanced Authentication Engine with liveness, lockout, risk, and fallback."""

from typing import Optional, Tuple
import numpy as np

from Core.config.settings import SystemSettings
from Core.detection.detector_interface import IFaceDetector
from Core.recognition.recognizer_interface import IFeatureExtractor
from Core.recognition.matcher import VectorMatcher
from Core.encryption.key_manager import KeyManager
from Core.encryption.embedding_encryptor import EmbeddingEncryptor
from Core.liveness.liveness_interface import ILivenessDetector
from Core.storage.database_interface import IDatabaseStorage
from Core.authentication.attempt_tracker import AttemptTracker
from Core.authentication.risk_evaluator import RiskEvaluator
from Core.authentication.password_fallback import PasswordFallback
from Core.utils.audit_logger import AuditLogger
from Core.utils.crypto_utils import generate_salt
from Core.utils.logger import get_logger

logger = get_logger("AuthenticationEngine")


class AuthenticationEngine:
    """Orchestrates face enrollment and multi-layered authentication pipeline."""

    def __init__(
        self,
        settings: SystemSettings,
        detector: IFaceDetector,
        extractor: IFeatureExtractor,
        storage: IDatabaseStorage,
        liveness_detector: Optional[ILivenessDetector] = None,
    ):
        self.settings = settings
        self.detector = detector
        self.extractor = extractor
        self.storage = storage
        self.matcher = VectorMatcher()
        self.liveness_detector = liveness_detector
        self.tracker = AttemptTracker(
            settings.security.max_auth_attempts,
            settings.security.lockout_duration_seconds,
        )
        self.risk_eval = RiskEvaluator(settings.security.matching_threshold)
        self.password_handler = PasswordFallback(settings.security.password_hash_iterations)
        self.audit = AuditLogger(settings.audit_log_path)

    def enroll_user(
        self, user_id: str, username: str, secret: str, frame: np.ndarray,
        password: Optional[str] = None,
    ) -> bool:
        """Enroll new user template from frame with optional password fallback."""
        faces = self.detector.detect_faces(frame)
        if not faces:
            logger.warning("No face detected during enrollment.")
            self.audit.log_enrollment(user_id, success=False)
            return False

        embedding = self.extractor.extract_embedding(frame, faces[0])
        salt = generate_salt()
        key_mgr = KeyManager(master_secret=secret, salt=salt)
        encryptor = EmbeddingEncryptor(key_mgr.get_key())

        encrypted_payload = encryptor.encrypt_vector(embedding)
        success = self.storage.save_user(user_id, username, encrypted_payload, salt)

        if success and password:
            pw_hash = self.password_handler.hash_password(password)
            self.storage.save_password_hash(user_id, pw_hash)

        self.audit.log_enrollment(user_id, success=success)
        if success:
            logger.info(f"User '{username}' ({user_id}) enrolled successfully.")
        return success

    def authenticate_user(
        self, user_id: str, secret: str, frame: np.ndarray
    ) -> Tuple[bool, float]:
        """Authenticate user with liveness, risk scoring, and lockout."""
        if self.tracker.is_locked(user_id):
            logger.warning(f"User '{user_id}' is locked out.")
            return False, 0.0

        faces = self.detector.detect_faces(frame)
        if not faces:
            logger.warning("No face detected during authentication.")
            return False, 0.0

        # Liveness check
        liveness_confidence = 1.0
        if self.liveness_detector and self.settings.security.liveness_required:
            result = self.liveness_detector.check_liveness(frame, faces[0])
            self.audit.log_liveness_check(user_id, result.is_live, result.confidence)
            liveness_confidence = result.confidence
            if not result.is_live:
                self.tracker.record_failure(user_id)
                return False, 0.0

        # Adaptive threshold
        remaining = self.tracker.get_remaining_attempts(user_id)
        failed = self.settings.security.max_auth_attempts - remaining
        threshold = self.risk_eval.get_adjusted_threshold(failed, liveness_confidence)

        # Embedding comparison
        user_data = self.storage.get_all_users()
        user_record = next((u for u in user_data if u[0] == user_id), None)
        if not user_record:
            return False, 0.0

        _, _, enc_payload, salt = user_record
        key_mgr = KeyManager(master_secret=secret, salt=salt)
        encryptor = EmbeddingEncryptor(key_mgr.get_key())

        try:
            stored_embedding = encryptor.decrypt_vector(enc_payload)
        except Exception:
            self.tracker.record_failure(user_id)
            return False, 0.0

        current_embedding = self.extractor.extract_embedding(frame, faces[0])
        similarity = self.matcher.cosine_similarity(stored_embedding, current_embedding)
        passed = similarity >= threshold

        if passed:
            self.tracker.record_success(user_id)
        else:
            locked = self.tracker.record_failure(user_id)
            if locked:
                self.audit.log_lockout(user_id)

        self.audit.log_auth_attempt(user_id, passed, similarity)
        return passed, similarity

    def authenticate_with_password(self, user_id: str, password: str) -> bool:
        """Fallback authentication using stored password hash."""
        stored_hash = self.storage.get_password_hash(user_id)
        if not stored_hash:
            self.audit.log_password_fallback(user_id, success=False)
            return False
        result = self.password_handler.verify_password(password, stored_hash)
        self.audit.log_password_fallback(user_id, success=result)
        if result:
            self.tracker.record_success(user_id)
        return result
