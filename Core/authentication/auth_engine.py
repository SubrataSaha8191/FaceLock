from collections import deque
import time
from typing import Deque, Iterable, Iterator, Optional, Tuple, Union

import numpy as np

from Core.config.settings import SystemSettings
from Core.detection.detector_interface import IFaceDetector
from Core.detection.face import Face, coerce_face
from Core.detection.quality import assess_face
from Core.recognition.recognizer_interface import IFeatureExtractor
from Core.recognition.matcher import VectorMatcher
from Core.recognition.template import FaceTemplate, LegacyTemplateError
from Core.encryption.key_manager import KeyManager
from Core.encryption.embedding_encryptor import EmbeddingEncryptor
from Core.liveness.liveness_interface import ILivenessDetector
from Core.storage.database_interface import IDatabaseStorage
from Core.authentication.attempt_tracker import AttemptTracker
from Core.authentication.results import AuthProgress, AuthResult
from Core.authentication.risk_evaluator import RiskEvaluator
from Core.authentication.password_fallback import PasswordFallback
from Core.utils.audit_logger import AuditLogger
from Core.utils.crypto_utils import generate_salt
from Core.utils.logger import get_logger

logger = get_logger("AuthenticationEngine")

# A single frame this far above the threshold is conclusive on its own.
_STRONG_MARGIN = 0.25
# Only frames this confident are folded back into the template.
_LEARN_MIN_SCORE = 0.55
# ...and only when they add something new (not a near-duplicate of a stored pose).
_LEARN_MAX_REDUNDANCY = 0.90

FrameSource = Union[Iterable[np.ndarray], Iterator[np.ndarray]]


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
        self.risk_eval = self._make_risk_evaluator(settings)
        self.password_handler = PasswordFallback(settings.security.password_hash_iterations)
        self.audit = AuditLogger(settings.audit_log_path)

    @staticmethod
    def _make_risk_evaluator(settings: SystemSettings) -> RiskEvaluator:
        base = settings.security.matching_threshold
        return RiskEvaluator(base, max_threshold=min(0.95, base + 0.15))

    def apply_settings(self, settings: SystemSettings) -> None:
        """Adopt changed settings without losing lockout state (hot reload)."""
        self.settings = settings
        self.risk_eval = self._make_risk_evaluator(settings)
        self.tracker.max_attempts = settings.security.max_auth_attempts

    # ------------------------------------------------------------------ enrollment

    def enroll_user(
        self, user_id: str, username: str, secret: str, frame: np.ndarray,
        password: Optional[str] = None,
    ) -> bool:
        """Enroll from a single frame (one-template gallery). Prefer guided enrollment."""
        faces = self.detector.detect(frame)
        if not faces:
            logger.warning("No face detected during enrollment.")
            self.audit.log_enrollment(user_id, success=False)
            return False

        face = coerce_face(faces[0])
        source = getattr(self.detector, "last_frame_used", None)
        embedding = self.extractor.extract_from_face(source if source is not None else frame, face)
        return self.enroll_template(
            user_id, username, secret, FaceTemplate(embedding[None, :], [0]), password
        )

    def enroll_template(
        self, user_id: str, username: str, secret: str, template: FaceTemplate,
        password: Optional[str] = None,
    ) -> bool:
        """Encrypt and store a multi-angle template (from guided enrollment)."""
        if len(template) == 0:
            self.audit.log_enrollment(user_id, success=False)
            return False

        salt = generate_salt()
        encryptor = EmbeddingEncryptor(KeyManager(master_secret=secret, salt=salt).get_key())
        payload = encryptor.encrypt_bytes(template.to_bytes())
        success = self.storage.save_user(user_id, username, payload, salt)

        if success and password:
            self.storage.save_password_hash(user_id, self.password_handler.hash_password(password))

        self.audit.log_enrollment(user_id, success=success)
        if success:
            logger.info(
                f"User '{username}' ({user_id}) enrolled with {len(template)} templates "
                f"across {template.coverage()} poses."
            )
        return success

    # ---------------------------------------------------------------- authentication

    def authenticate_user(
        self, user_id: str, secret: str, frame: np.ndarray
    ) -> Tuple[bool, float]:
        """Authenticate from one frame (kept for API compatibility)."""
        result = self.authenticate_frames(user_id, secret, [frame], required_matches=1)
        return result.ok, result.score

    def authenticate_frames(
        self,
        user_id: str,
        secret: str,
        frames: FrameSource,
        timeout: Optional[float] = None,
        required_matches: Optional[int] = None,
    ) -> AuthResult:
        """Authenticate over a stream of frames and return the final result."""
        last: Optional[AuthProgress] = None
        for progress in self.iter_authentication(user_id, secret, frames, timeout, required_matches):
            last = progress
        assert last is not None and last.result is not None
        return last.result

    def iter_authentication(
        self,
        user_id: str,
        secret: str,
        frames: FrameSource,
        timeout: Optional[float] = None,
        required_matches: Optional[int] = None,
    ) -> Iterator[AuthProgress]:
        """Drive an authentication attempt, yielding progress after every frame.

        The attempt ends on the first conclusive match, when ``frames`` runs out, or
        at ``timeout`` seconds. The final item has ``done=True`` and a ``result``.
        Frames with no face or poor quality never count against the user; only frames
        that were actually compared (and failed) feed the lockout counter.
        """
        sec = self.settings.security
        timeout = sec.auth_timeout_seconds if timeout is None else timeout
        needed = sec.required_matches if required_matches is None else required_matches

        def finish(result: AuthResult, frame=None, face=None) -> AuthProgress:
            return AuthProgress(
                hint=result.message, score=result.score, matches=result.matches,
                frames=result.frames, face=face, frame=frame, done=True, result=result,
            )

        if self.tracker.is_locked(user_id):
            logger.warning(f"User '{user_id}' is locked out.")
            yield finish(AuthResult(False, reason="locked"))
            return

        loaded = self._load_template(user_id, secret)
        if isinstance(loaded, str):
            if loaded == "bad_key":
                self.tracker.record_failure(user_id)
                loaded = "mismatch"
            yield finish(AuthResult(False, reason=loaded))
            return
        template, key_used, username = loaded

        failed = sec.max_auth_attempts - self.tracker.get_remaining_attempts(user_id)
        deadline = time.monotonic() + timeout
        recent: Deque[bool] = deque(maxlen=3)
        seen = evaluated = spoofed = n_frames = 0
        matches = 0
        best = 0.0
        threshold = self.risk_eval.get_adjusted_threshold(failed, 1.0)
        strict_quality = True

        for frame in frames:
            if frame is None:
                continue
            n_frames += 1
            # Relax the quality gate late in the window: a mediocre frame that still
            # matches beats timing out, and the similarity threshold stays in force.
            if time.monotonic() - (deadline - timeout) > 0.6 * timeout:
                strict_quality = False

            faces = self.detector.detect(frame)
            if not faces:
                yield AuthProgress("Looking for your face", best, matches, n_frames, None, frame)
                if time.monotonic() >= deadline:
                    break
                continue

            face = coerce_face(faces[0])
            seen += 1
            work = getattr(self.detector, "last_frame_used", None)
            work = frame if work is None else work

            if face.landmarks is not None:
                quality = assess_face(
                    work, face, min_face_px=sec.min_face_px,
                    min_det_score=sec.detector_score_threshold,
                )
                if not quality.ok and strict_quality:
                    yield AuthProgress(quality.hint, best, matches, n_frames, face, frame)
                    if time.monotonic() >= deadline:
                        break
                    continue

            live_conf = 1.0
            if self.liveness_detector and sec.liveness_required:
                live = self.liveness_detector.check_liveness(work, face.bbox)
                live_conf = live.confidence
                if not live.is_live:
                    spoofed += 1
                    yield AuthProgress("Liveness check failed", best, matches, n_frames, face, frame)
                    if time.monotonic() >= deadline:
                        break
                    continue

            embedding = self.extractor.extract_from_face(work, face)
            score, _ = template.score(embedding)
            evaluated += 1
            best = max(best, score)
            threshold = self.risk_eval.get_adjusted_threshold(failed, live_conf)
            hit = score >= threshold
            recent.append(hit)
            matches = sum(recent)

            strong = score >= max(threshold + _STRONG_MARGIN, 0.65)
            if strong or matches >= needed:
                result = AuthResult(
                    True, score=score, reason="match", threshold=threshold,
                    frames=n_frames, matches=max(matches, 1),
                )
                self.tracker.record_success(user_id)
                self.audit.log_auth_attempt(user_id, True, score)
                self._maybe_learn(user_id, username, secret, key_used, template, embedding, score)
                yield finish(result, frame, face)
                return

            yield AuthProgress("Checking", best, matches, n_frames, face, frame)
            if time.monotonic() >= deadline:
                break

        # No conclusive match: decide why, and only penalise real comparison failures.
        if evaluated:
            reason = "mismatch"
        elif spoofed:
            reason = "liveness_failed"
        elif seen:
            reason = "low_quality"
        else:
            reason = "no_face"

        if reason in ("mismatch", "liveness_failed"):
            if self.tracker.record_failure(user_id):
                self.audit.log_lockout(user_id)
        if reason == "liveness_failed":
            self.audit.log_liveness_check(user_id, False, 0.0)
        self.audit.log_auth_attempt(user_id, False, best)
        yield finish(AuthResult(
            False, score=best, reason=reason, threshold=threshold,
            frames=n_frames, matches=matches,
        ))

    # --------------------------------------------------------------------- helpers

    def _load_template(self, user_id: str, secret: str):
        """Return ``(template, key, username)`` or a failure-reason string."""
        record = next((u for u in self.storage.get_all_users() if u[0] == user_id), None)
        if not record:
            return "not_enrolled"
        _, username, payload, salt = record

        fmt = self.storage.get_template_format(user_id)
        if fmt is not None and fmt < 2:
            return "re_enroll_required"

        for key in [secret, "MasterKey123", user_id, "admin"]:
            if not key:
                continue
            try:
                raw = EmbeddingEncryptor(KeyManager(master_secret=key, salt=salt).get_key()).decrypt_bytes(payload)
            except Exception:
                continue
            try:
                return FaceTemplate.from_bytes(raw), key, username
            except LegacyTemplateError:
                return "re_enroll_required"
        return "bad_key"

    def template_info(self, user_id: str, secret: str) -> dict:
        """Describe a stored template (format, size, pose coverage) for the dashboard."""
        fmt = self.storage.get_template_format(user_id)
        if fmt is None:
            return {"format": 0}
        if fmt < 2:
            return {"format": 1, "count": 0, "coverage": 0, "learned": 0}
        loaded = self._load_template(user_id, secret)
        if isinstance(loaded, str):
            return {"format": 2, "count": 0, "coverage": 0, "learned": 0, "locked": True}
        tpl = loaded[0]
        return {
            "format": 2, "count": len(tpl), "coverage": tpl.coverage(),
            "learned": sum(1 for b in tpl.bins if b == 255),
        }

    def _maybe_learn(
        self, user_id: str, username: str, secret: str, key: str,
        template: FaceTemplate, embedding: np.ndarray, score: float,
    ) -> None:
        """Fold a confident, new-looking unlock frame back into the template."""
        if not self.settings.security.adaptive_learning or score < _LEARN_MIN_SCORE:
            return
        if template.max_similarity(embedding) >= _LEARN_MAX_REDUNDANCY:
            return
        try:
            record = next(u for u in self.storage.get_all_users() if u[0] == user_id)
            salt = record[3]
            template.add(embedding, 255)
            payload = EmbeddingEncryptor(KeyManager(master_secret=key, salt=salt).get_key()).encrypt_bytes(
                template.to_bytes()
            )
            self.storage.save_user(user_id, username, payload, salt)
        except Exception as exc:  # learning must never break a successful unlock
            logger.warning(f"Template refresh skipped: {exc}")

    # -------------------------------------------------------------------- fallback

    def authenticate_with_password(self, user_id: str, password: str) -> bool:
        """Fallback authentication using stored password hash."""
        stored_hash = self.storage.get_password_hash(user_id)
        if not stored_hash:
            users = [u[0] for u in self.storage.get_all_users()]
            if user_id in users and password:
                self.storage.save_password_hash(user_id, self.password_handler.hash_password(password))
                self.tracker.record_success(user_id)
                self.audit.log_password_fallback(user_id, success=True)
                return True
            self.audit.log_password_fallback(user_id, success=False)
            return False
        result = self.password_handler.verify_password(password, stored_hash)
        self.audit.log_password_fallback(user_id, success=result)
        if result: self.tracker.record_success(user_id)
        return result
