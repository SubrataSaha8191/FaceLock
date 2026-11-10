"""Guided, Face ID-style enrollment.

The user first looks straight at the camera (centre captures), then slowly moves
their head in a circle. The circle is split into eight sectors; each sector must
collect a couple of sharp, well-lit, same-person captures. The result is a
:class:`FaceTemplate` that covers the face from every direction, which is what
makes unlocking work at an angle.

Directions are described the way the user sees them in a *mirrored* preview:
"right" means the user's own right. Sector ``k`` sits at ``k * 45`` degrees,
counter-clockwise from 3 o'clock on the on-screen ring.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from Core.detection.detector_interface import IFaceDetector
from Core.detection.face import Face, coerce_face
from Core.detection.quality import assess_face
from Core.recognition.recognizer_interface import IFeatureExtractor
from Core.recognition.template import FaceTemplate

CENTER_NEEDED = 4
SECTOR_NEEDED = 2
NUM_SECTORS = 8
SECTOR_NAMES = ["right", "up and right", "up", "up and left",
                "left", "down and left", "down", "down and right"]

# Degrees of head rotation (from the centre pose) that reach the ring's edge.
YAW_SCALE = 15.0
PITCH_SCALE = 9.0
# A centre capture must be within this many degrees of the running baseline.
CENTER_YAW_TOL = 10.0
CENTER_PITCH_TOL = 8.0
# Floor on similarity to the centre captures: rejects a swapped-in stranger or a
# mis-detection while tolerating the large drop that real profile views cause.
IDENTITY_FLOOR = 0.20
MIN_FRAME_GAP = 3  # frames between two captures


@dataclass
class EnrollmentStatus:
    """Snapshot of enrollment progress after processing one frame."""

    phase: str = "center"                      # center | rotate | done
    progress: float = 0.0                      # 0..1 overall
    center_count: int = 0
    sector_counts: List[int] = field(default_factory=lambda: [0] * NUM_SECTORS)
    hint: str = "Position your face in the frame"
    face: Optional[Face] = None
    pose_uv: Tuple[float, float] = (0.0, 0.0)  # on-screen ring coordinates (unit = ring edge)
    target_sector: Optional[int] = None
    captured: bool = False
    face_ok: bool = False
    can_finish: bool = False

    def to_dict(self, frame_size: Tuple[int, int]) -> dict:
        """JSON-friendly form for the dashboard (face box normalised to 0..1)."""
        fw, fh = frame_size
        box = None
        lms = None
        if self.face is not None:
            x, y, w, h = self.face.bbox
            box = [x / fw, y / fh, w / fw, h / fh]
            if self.face.landmarks is not None:
                lms = [[float(px) / fw, float(py) / fh] for px, py in self.face.landmarks]
        return {
            "phase": self.phase,
            "progress": round(self.progress, 4),
            "centerCount": self.center_count,
            "centerNeeded": CENTER_NEEDED,
            "sectorCounts": self.sector_counts,
            "sectorNeeded": SECTOR_NEEDED,
            "hint": self.hint,
            "box": box,
            "landmarks": lms,
            "poseUV": [round(self.pose_uv[0], 3), round(self.pose_uv[1], 3)],
            "targetSector": self.target_sector,
            "captured": self.captured,
            "faceOk": self.face_ok,
            "canFinish": self.can_finish,
        }


class EnrollmentSession:
    """Feed frames in; read status out; call :meth:`build_template` when done."""

    def __init__(
        self,
        detector: IFaceDetector,
        extractor: IFeatureExtractor,
        min_face_px: int = 90,
        min_sectors_to_finish: int = 5,
    ):
        self.detector = detector
        self.extractor = extractor
        self.min_face_px = min_face_px
        self.min_sectors_to_finish = min_sectors_to_finish

        self._embeddings: List[np.ndarray] = []
        self._bins: List[int] = []
        self._center: List[np.ndarray] = []
        self._center_poses: List[Tuple[float, float]] = []
        self._sector_counts = [0] * NUM_SECTORS
        self._baseline: Optional[Tuple[float, float]] = None
        self._target: Optional[int] = None  # sticky: the sector we are asking the user to reach
        self._frame_no = 0
        self._last_capture_frame = -MIN_FRAME_GAP
        self.status = EnrollmentStatus()

    # ------------------------------------------------------------------- queries

    @property
    def center_done(self) -> bool:
        return len(self._center) >= CENTER_NEEDED

    @property
    def sectors_filled(self) -> int:
        return sum(1 for c in self._sector_counts if c >= SECTOR_NEEDED)

    @property
    def complete(self) -> bool:
        return self.center_done and self.sectors_filled == NUM_SECTORS

    @property
    def can_finish(self) -> bool:
        return self.center_done and self.sectors_filled >= self.min_sectors_to_finish

    def build_template(self) -> FaceTemplate:
        """Return the captured gallery (call once :attr:`complete` or :attr:`can_finish`)."""
        if not self._embeddings:
            return FaceTemplate()
        return FaceTemplate(np.vstack(self._embeddings), list(self._bins))

    # ------------------------------------------------------------------- process

    def process(self, frame: np.ndarray) -> EnrollmentStatus:
        """Analyse one camera frame and capture a template from it when appropriate."""
        self._frame_no += 1
        st = EnrollmentStatus(
            phase=self._phase(),
            center_count=len(self._center),
            sector_counts=list(self._sector_counts),
            can_finish=self.can_finish,
        )
        st.progress = self._progress()

        if st.phase == "done":
            st.hint = "All set"
            self.status = st
            return st

        faces = self.detector.detect(frame)
        if not faces:
            st.hint = "Position your face in the frame"
            self.status = st
            return st

        face = coerce_face(faces[0])
        st.face = face
        if len(faces) > 1 and coerce_face(faces[1]).area > 0.4 * face.area:
            st.hint = "Make sure only you are in view"
            self.status = st
            return st

        work = getattr(self.detector, "last_frame_used", None)
        work = frame if work is None else work

        if face.landmarks is not None:
            q = assess_face(work, face, min_face_px=self.min_face_px)
            if not q.ok:
                st.hint = q.hint or "Face the camera"
                self.status = st
                return st
        st.face_ok = True

        if st.phase == "center":
            self._process_center(work, face, st)
        else:
            self._process_rotate(work, face, st)

        st.phase = self._phase()
        st.center_count = len(self._center)
        st.sector_counts = list(self._sector_counts)
        st.can_finish = self.can_finish
        st.progress = self._progress()
        if st.phase == "done":
            st.hint = "All set"
        self.status = st
        return st

    # ------------------------------------------------------------------ internals

    def _phase(self) -> str:
        if not self.center_done:
            return "center"
        return "done" if self.complete else "rotate"

    def _progress(self) -> float:
        center = min(len(self._center), CENTER_NEEDED) / CENTER_NEEDED
        sectors = sum(min(c, SECTOR_NEEDED) for c in self._sector_counts) / (NUM_SECTORS * SECTOR_NEEDED)
        return 0.2 * center + 0.8 * sectors

    def _may_capture(self) -> bool:
        return self._frame_no - self._last_capture_frame >= MIN_FRAME_GAP

    def _embed(self, work: np.ndarray, face: Face) -> np.ndarray:
        return self.extractor.extract_from_face(work, face)

    def _store(self, emb: np.ndarray, pose_bin: int) -> None:
        self._embeddings.append(emb)
        self._bins.append(pose_bin)
        self._last_capture_frame = self._frame_no

    def _process_center(self, work: np.ndarray, face: Face, st: EnrollmentStatus) -> None:
        st.hint = "Look straight at the camera"
        if face.pose_valid:
            if self._baseline is None:
                self._baseline = (face.yaw, face.pitch)
            if (abs(face.yaw - self._baseline[0]) > CENTER_YAW_TOL
                    or abs(face.pitch - self._baseline[1]) > CENTER_PITCH_TOL):
                return
        if not self._may_capture():
            return

        emb = self._embed(work, face)
        if self._center and float(np.mean([e @ emb for e in self._center])) < 0.3:
            st.hint = "Make sure only you are in view"
            return
        self._center.append(emb)
        if face.pose_valid:
            self._center_poses.append((face.yaw, face.pitch))
        self._store(emb, 0)
        st.captured = True
        if self.center_done:
            if self._center_poses:
                self._baseline = (
                    float(np.median([p[0] for p in self._center_poses])),
                    float(np.median([p[1] for p in self._center_poses])),
                )
            st.hint = "Now slowly move your head in a circle"

    def _process_rotate(self, work: np.ndarray, face: Face, st: EnrollmentStatus) -> None:
        if not face.pose_valid:
            st.hint = "Face the camera"
            return
        yaw0, pitch0 = self._baseline if self._baseline is not None else (0.0, 0.0)
        u = -(face.yaw - yaw0) / YAW_SCALE      # mirrored preview: nose to the right => +u
        v = (face.pitch - pitch0) / PITCH_SCALE  # looking up => +v
        st.pose_uv = (u, v)
        radius = math.hypot(u, v)
        current = self._sector_of(u, v) if radius >= 1.0 else None
        st.target_sector = self._sticky_target(u, v, radius)
        st.hint = self._rotate_hint(st.target_sector)

        if current is None or self._sector_counts[current] >= SECTOR_NEEDED or not self._may_capture():
            return

        emb = self._embed(work, face)
        if self._center and float(np.mean([e @ emb for e in self._center])) < IDENTITY_FLOOR:
            st.hint = "Make sure only you are in view"
            return
        self._sector_counts[current] += 1
        self._store(emb, current + 1)
        st.captured = True
        st.target_sector = self._sticky_target(u, v, radius)
        st.hint = self._rotate_hint(st.target_sector)

    @staticmethod
    def _rotate_hint(target: Optional[int]) -> str:
        return "All set" if target is None else f"Turn your head {SECTOR_NAMES[target]}"

    def _sticky_target(self, u: float, v: float, radius: float) -> Optional[int]:
        """Keep asking for the same direction until it is captured, so guidance doesn't flip."""
        if self._target is not None and self._sector_counts[self._target] < SECTOR_NEEDED:
            return self._target
        self._target = self._next_target(u, v, radius)
        return self._target

    @staticmethod
    def _sector_of(u: float, v: float) -> int:
        return int(round(math.atan2(v, u) / (math.pi / 4))) % NUM_SECTORS

    def _next_target(self, u: float, v: float, radius: float) -> Optional[int]:
        """Nearest unfinished sector, measured around the circle from the current pose."""
        open_sectors = [k for k, c in enumerate(self._sector_counts) if c < SECTOR_NEEDED]
        if not open_sectors:
            return None
        if radius < 0.4:
            return open_sectors[0]
        here = self._sector_of(u, v)

        def circular_gap(k: int) -> int:
            d = abs(k - here) % NUM_SECTORS
            return min(d, NUM_SECTORS - d)

        return min(open_sectors, key=circular_gap)
