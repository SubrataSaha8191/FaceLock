"""Multi-angle templates, streaming authentication and guided enrollment."""

import sqlite3
from pathlib import Path

import numpy as np
import pytest

from Core.authentication.auth_engine import AuthenticationEngine
from Core.config.loader import ConfigLoader
from Core.config.settings import CONFIG_VERSION, SystemSettings
from Core.detection.detector_interface import IFaceDetector
from Core.detection.face import Face
from Core.detection.quality import assess_face
from Core.enrollment import CENTER_NEEDED
from Core.enrollment.session import NUM_SECTORS, SECTOR_NEEDED, EnrollmentSession
from Core.liveness.liveness_interface import ILivenessDetector
from Core.liveness.liveness_result import LivenessResult
from Core.recognition.recognizer_interface import IFeatureExtractor
from Core.recognition.template import FaceTemplate, LegacyTemplateError
from Core.storage.encrypted_sqlite_storage import EncryptedSQLiteStorage

FRAME = np.full((120, 160, 3), 128, dtype=np.uint8)


def unit(v):
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v)


def person(seed):
    return unit(np.random.default_rng(seed).normal(size=128))


def near(base, noise, seed):
    return unit(base + noise * np.random.default_rng(seed).normal(size=128) / np.sqrt(128))


class Scripted(IFaceDetector):
    """Detector that replays a scripted list of per-frame detections."""

    def __init__(self, script):
        self.script = list(script)

    def detect_faces(self, frame):
        return [f.bbox for f in self.detect(frame)]

    def detect(self, frame):
        item = self.script.pop(0) if self.script else []
        return item if isinstance(item, list) else [item]


class FromFace(IFeatureExtractor):
    def extract_embedding(self, frame, bbox):  # pragma: no cover - unused
        raise NotImplementedError

    def extract_from_face(self, frame, face):
        return face.extra["emb"]


def face(emb, yaw=0.0, pitch=0.0, size=120):
    f = Face(bbox=(10, 10, size, size), score=0.95, pose_valid=True, yaw=yaw, pitch=pitch)
    f.extra["emb"] = emb
    return f


class Live(ILivenessDetector):
    def __init__(self, ok=True):
        self.ok = ok

    def check_liveness(self, frame, bbox):
        return LivenessResult(self.ok, 0.9 if self.ok else 0.1, "t")


def make_engine(tmp_path, script, liveness=None):
    settings = SystemSettings(data_dir=tmp_path, db_name="t.db")
    settings.security.auth_timeout_seconds = 5
    storage = EncryptedSQLiteStorage(settings.db_path)
    return AuthenticationEngine(settings, Scripted(script), FromFace(), storage, liveness)


def enroll(engine, user, emb_list, bins=None):
    tpl = FaceTemplate(np.vstack(emb_list), bins)
    assert engine.enroll_template(user, user.title(), "pw", tpl)


def run(engine, user, n=6, **kw):
    return engine.authenticate_frames(user, "pw", iter([FRAME] * n), **kw)


# ------------------------------------------------------------------ templates


def test_template_roundtrip_and_scoring():
    base = person(1)
    tpl = FaceTemplate(np.vstack([near(base, 0.2, i) for i in range(5)]), [0, 1, 2, 3, 255])
    again = FaceTemplate.from_bytes(tpl.to_bytes())
    assert len(again) == 5 and again.bins == [0, 1, 2, 3, 255]
    assert again.coverage() == 4  # learned entries (255) don't count as enrolled poses
    assert again.score(base)[0] > 0.9
    assert again.score(person(2))[0] < 0.3


def test_template_rejects_legacy_payload():
    legacy = np.ones(128, dtype=np.float32).tobytes()
    with pytest.raises(LegacyTemplateError):
        FaceTemplate.from_bytes(legacy)


def test_template_is_bounded_and_drops_learned_first():
    tpl = FaceTemplate(np.vstack([person(i) for i in range(48)]), [1] * 47 + [255])
    tpl.add(person(99), 255)
    assert len(tpl) == 48
    assert tpl.bins.count(255) == 1


def test_single_outlier_template_cannot_carry_a_stranger():
    me = person(3)
    stranger = person(4)
    tpl = FaceTemplate(np.vstack([me, near(me, 0.1, 1), stranger]))
    # The stranger matches template #3 perfectly but not the other two.
    assert tpl.score(stranger)[0] < 0.6


# --------------------------------------------------------------- authentication


def test_unlocks_from_any_enrolled_angle(tmp_path):
    me = person(10)
    angles = [near(me, 0.35 * k, k) for k in range(1, 6)]  # increasingly off-axis views
    engine = make_engine(tmp_path, [])
    enroll(engine, "u", [me] + angles, [0, 1, 2, 3, 4, 5])
    for emb in angles:
        engine.detector.script = [face(near(emb, 0.1, 50))] * 6
        res = run(engine, "u")
        assert res.ok, (res.reason, res.score)


def test_stranger_is_rejected_and_counts_once(tmp_path):
    engine = make_engine(tmp_path, [face(person(20))] * 8)
    enroll(engine, "u", [person(10)])
    res = run(engine, "u", n=8)
    assert not res.ok and res.reason == "mismatch"
    # One failed *attempt*, not one per frame: 8 frames compared but a single strike.
    assert engine.tracker.get_remaining_attempts("u") == engine.settings.security.max_auth_attempts - 1


def test_borderline_frames_never_unlock(tmp_path):
    me = person(10)
    weak = near(me, 1.6, 5)
    engine = make_engine(tmp_path, [])
    engine.settings.security.matching_threshold = 0.9
    engine.apply_settings(engine.settings)
    enroll(engine, "u", [me])
    assert float(weak @ me) < engine.settings.security.matching_threshold
    engine.detector.script = [face(weak)] * 5
    assert not run(engine, "u", n=5).ok


def test_one_strong_frame_is_conclusive(tmp_path):
    me = person(10)
    engine = make_engine(tmp_path, [face(near(me, 0.1, 1))])
    enroll(engine, "u", [me])
    res = run(engine, "u", n=3)
    assert res.ok and res.reason == "match" and res.frames == 1


def test_no_face_never_counts_against_the_user(tmp_path):
    engine = make_engine(tmp_path, [[]] * 5)
    enroll(engine, "u", [person(10)])
    res = run(engine, "u", n=5)
    assert res.reason == "no_face" and not res.ok
    assert engine.tracker.get_remaining_attempts("u") == engine.settings.security.max_auth_attempts


def test_liveness_failure_is_a_strike(tmp_path):
    me = person(10)
    engine = make_engine(tmp_path, [face(me)] * 4, liveness=Live(False))
    enroll(engine, "u", [me])
    res = run(engine, "u", n=4)
    assert res.reason == "liveness_failed"
    assert engine.tracker.get_remaining_attempts("u") == engine.settings.security.max_auth_attempts - 1


def test_lockout_blocks_without_touching_frames(tmp_path):
    engine = make_engine(tmp_path, [])
    enroll(engine, "u", [person(10)])
    for _ in range(engine.settings.security.max_auth_attempts):
        engine.tracker.record_failure("u")
    assert run(engine, "u").reason == "locked"


def test_old_format_profile_asks_to_reenroll(tmp_path):
    engine = make_engine(tmp_path, [face(person(1))])
    enroll(engine, "u", [person(1)])
    with sqlite3.connect(engine.settings.db_path) as c:
        c.execute("UPDATE users SET template_format = 1 WHERE user_id = 'u'")
    res = run(engine, "u")
    assert res.reason == "re_enroll_required" and not res.ok
    assert engine.template_info("u", "pw")["format"] == 1


def test_adaptive_learning_adds_new_looking_confident_frames(tmp_path):
    me = person(10)
    drift = near(me, 0.55, 3)
    assert 0.55 <= float(me @ drift) < 0.9
    engine = make_engine(tmp_path, [face(drift)])
    enroll(engine, "u", [me])
    assert run(engine, "u", n=1).ok
    info = engine.template_info("u", "pw")
    assert info["count"] == 2 and info["learned"] == 1


def test_adaptive_learning_skips_near_duplicates_and_can_be_disabled(tmp_path):
    me = person(10)
    engine = make_engine(tmp_path, [face(near(me, 0.05, 1))])
    enroll(engine, "u", [me])
    assert run(engine, "u", n=1).ok
    assert engine.template_info("u", "pw")["count"] == 1

    drift = near(me, 0.55, 3)
    engine2 = make_engine(tmp_path / "b", [face(drift)])
    engine2.settings.security.adaptive_learning = False
    enroll(engine2, "u", [me])
    assert run(engine2, "u", n=1).ok
    assert engine2.template_info("u", "pw")["count"] == 1


# ------------------------------------------------------------ guided enrollment


def circle_script(person_emb, n_center=12, per_sector=8):
    """Frames of a user looking ahead, then circling their head (mirrored preview)."""
    frames = [face(near(person_emb, 0.1, i)) for i in range(n_center)]
    for k in range(NUM_SECTORS):
        ang = np.radians(45 * k)
        u, v = 1.6 * np.cos(ang), 1.6 * np.sin(ang)  # on-screen ring coordinates
        yaw, pitch = -u * 15.0, v * 9.0
        for j in range(per_sector):
            frames.append(face(near(person_emb, 0.5, 100 + k * 20 + j), yaw=yaw, pitch=pitch))
    return frames


def test_guided_enrollment_completes_all_sectors():
    me = person(30)
    det = Scripted(circle_script(me))
    session = EnrollmentSession(det, FromFace())
    hints = set()
    st = None
    for _ in range(len(det.script)):
        st = session.process(FRAME)
        hints.add(st.hint)
        if session.complete:
            break
    assert session.complete and st.phase == "done" and st.progress == pytest.approx(1.0)
    tpl = session.build_template()
    assert tpl.coverage() == NUM_SECTORS + 1  # centre + every sector
    assert len(tpl) >= CENTER_NEEDED + NUM_SECTORS * SECTOR_NEEDED
    assert any("circle" in h for h in hints)


def test_guided_enrollment_sector_directions_follow_head_motion():
    me = person(30)
    session = EnrollmentSession(Scripted(circle_script(me, per_sector=0)), FromFace())
    for _ in range(12):
        session.process(FRAME)
    assert session.center_done
    # Turning to the user's right moves the nose to image-left (yaw < 0) = screen-right (+u) = sector 0.
    session.detector.script = [face(near(me, 0.4, i), yaw=-30.0) for i in range(6)]
    for _ in range(6):
        session.process(FRAME)
    assert session._sector_counts[0] >= 1
    assert sum(session._sector_counts[1:]) == 0


def test_enrollment_ignores_a_different_person_mid_session():
    me, other = person(30), person(31)
    det = Scripted([face(near(me, 0.1, i)) for i in range(12)])
    session = EnrollmentSession(det, FromFace())
    for _ in range(12):
        session.process(FRAME)
    det.script = [face(other, yaw=-30.0) for _ in range(8)]
    for _ in range(8):
        session.process(FRAME)
    assert sum(session._sector_counts) == 0


def test_enrollment_waits_for_a_single_person():
    me = person(30)
    a, b = face(near(me, 0.1, 1)), face(person(77))
    session = EnrollmentSession(Scripted([[a, b]] * 5), FromFace())
    st = None
    for _ in range(5):
        st = session.process(FRAME)
    assert len(session._embeddings) == 0 and "only you" in st.hint


def test_enrollment_can_finish_early_with_enough_coverage():
    me = person(30)
    script = circle_script(me, per_sector=8)
    session = EnrollmentSession(Scripted(script), FromFace(), min_sectors_to_finish=5)
    finished_early = False
    for _ in range(len(script)):
        session.process(FRAME)
        if session.can_finish and not session.complete:
            finished_early = True
            break
    assert finished_early and session.sectors_filled >= 5


# -------------------------------------------------------------- quality + config


def test_quality_gate_hints():
    bright = np.random.default_rng(0).integers(90, 170, (480, 640, 3), dtype=np.uint8)
    assert assess_face(bright, Face((200, 100, 200, 240), 0.95)).ok
    small = assess_face(bright, Face((200, 100, 40, 48), 0.95))
    assert "too_far" in small.reasons and small.hint
    dark = assess_face(np.full((480, 640, 3), 10, np.uint8), Face((200, 100, 200, 240), 0.95))
    assert "too_dark" in dark.reasons
    assert "cut_off" in assess_face(bright, Face((500, 100, 200, 240), 0.95)).reasons


def test_old_config_threshold_is_migrated(tmp_path: Path):
    cfg = tmp_path / "config.json"
    cfg.write_text('{"data_dir": "%s", "security": {"matching_threshold": 0.6}}' % tmp_path)
    loaded = ConfigLoader(cfg).load()
    assert loaded.security.matching_threshold == 0.40
    assert loaded.config_version == CONFIG_VERSION
    # A deliberately tuned v2 value is respected afterwards.
    loaded.security.matching_threshold = 0.5
    ConfigLoader(cfg).save(loaded)
    assert ConfigLoader(cfg).load().security.matching_threshold == 0.5


def test_legacy_database_gets_template_format_column(tmp_path: Path):
    db = tmp_path / "old.db"
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE users (user_id TEXT PRIMARY KEY, username TEXT NOT NULL, "
                  "encrypted_embedding BLOB NOT NULL, salt BLOB NOT NULL, "
                  "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("INSERT INTO users (user_id, username, encrypted_embedding, salt) "
                  "VALUES ('a','A',x'00',x'00')")
    storage = EncryptedSQLiteStorage(db)
    assert storage.get_template_format("a") == 1
    storage.save_user("b", "B", b"x", b"y")
    assert storage.get_template_format("b") == 2


def test_guidance_text_is_steady_while_capturing():
    """The hint must not flip between messages from frame to frame during a scan."""
    me = person(40)
    session = EnrollmentSession(Scripted(circle_script(me, per_sector=8)), FromFace())
    for _ in range(12):
        session.process(FRAME)
    assert session.center_done
    # Hold the head in one direction for many frames (several captures happen in between).
    session.detector.script = [face(near(me, 0.4, 500 + i), yaw=-30.0) for i in range(14)]
    hints = [session.process(FRAME).hint for _ in range(14)]
    assert "Hold still" not in hints
    changes = sum(1 for a, b in zip(hints, hints[1:]) if a != b)
    assert changes <= 1, hints  # at most the move on to the next direction once sector 0 is full


def test_target_direction_is_sticky():
    me = person(41)
    session = EnrollmentSession(Scripted(circle_script(me, per_sector=0)), FromFace())
    for _ in range(12):
        session.process(FRAME)
    targets = []
    for yaw in (-8.0, -3.0, 5.0, -2.0, 4.0, -6.0):  # wandering around the centre
        session.detector.script = [face(near(me, 0.2, 1), yaw=yaw)]
        targets.append(session.process(FRAME).target_sector)
    assert len(set(targets)) == 1, targets
