"""Multi-angle face template: a gallery of embeddings captured across head poses."""

import struct
from typing import List, Optional, Tuple

import numpy as np

MAGIC = b"FLT2"
_HEADER = struct.Struct("<4sHH")  # magic, count, dim
MAX_TEMPLATES = 48


class LegacyTemplateError(ValueError):
    """The stored template predates the deep-embedding pipeline and must be re-enrolled."""


class FaceTemplate:
    """A set of unit-norm embeddings, each tagged with the pose bin it was captured in.

    Pose bins: ``0`` = frontal, ``1..8`` = the eight head-direction sectors around it,
    ``255`` = learned during later successful unlocks.
    """

    def __init__(self, embeddings: Optional[np.ndarray] = None, bins: Optional[List[int]] = None):
        if embeddings is None or len(embeddings) == 0:
            self.embeddings = np.zeros((0, 128), dtype=np.float32)
            self.bins: List[int] = []
        else:
            arr = np.atleast_2d(np.asarray(embeddings, dtype=np.float32))
            self.embeddings = _normalize(arr)
            self.bins = list(bins) if bins is not None else [0] * len(arr)
            if len(self.bins) != len(arr):
                raise ValueError("bins and embeddings must have equal length")

    def __len__(self) -> int:
        return len(self.bins)

    def add(self, embedding: np.ndarray, pose_bin: int = 255) -> None:
        vec = _normalize(np.atleast_2d(np.asarray(embedding, dtype=np.float32)))
        if self.embeddings.shape[0] == 0:
            self.embeddings = vec
        else:
            self.embeddings = np.vstack([self.embeddings, vec])
        self.bins.append(pose_bin)
        self._trim()

    def _trim(self) -> None:
        """Keep the gallery bounded, dropping the oldest *learned* entries first."""
        while len(self.bins) > MAX_TEMPLATES:
            drop = next((i for i, b in enumerate(self.bins) if b == 255), 0)
            self.embeddings = np.delete(self.embeddings, drop, axis=0)
            del self.bins[drop]

    def score(self, probe: np.ndarray) -> Tuple[float, int]:
        """Similarity of a probe embedding to the gallery.

        Uses the mean of the best two matches (the single best when only one exists),
        so one odd template can't carry a wrong face over the threshold on its own.
        Returns ``(score, index_of_best_template)``.
        """
        if len(self) == 0:
            return 0.0, -1
        p = _normalize(np.atleast_2d(np.asarray(probe, dtype=np.float32)))[0]
        sims = self.embeddings @ p
        order = np.argsort(sims)[::-1]
        if len(sims) >= 3:
            return float((sims[order[0]] + sims[order[1]]) / 2.0), int(order[0])
        return float(sims[order[0]]), int(order[0])

    def max_similarity(self, probe: np.ndarray) -> float:
        if len(self) == 0:
            return 0.0
        p = _normalize(np.atleast_2d(np.asarray(probe, dtype=np.float32)))[0]
        return float(np.max(self.embeddings @ p))

    def coverage(self) -> int:
        """Number of distinct enrolled pose bins (excluding learned entries)."""
        return len({b for b in self.bins if b != 255})

    def to_bytes(self) -> bytes:
        n, d = self.embeddings.shape
        return (
            _HEADER.pack(MAGIC, n, d)
            + self.embeddings.astype("<f4").tobytes()
            + bytes(self.bins)
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "FaceTemplate":
        if len(data) >= _HEADER.size and data[:4] == MAGIC:
            _, n, d = _HEADER.unpack_from(data)
            off = _HEADER.size
            end = off + n * d * 4
            if len(data) < end + n:
                raise ValueError("Truncated face template.")
            emb = np.frombuffer(data[off:end], dtype="<f4").reshape(n, d).copy()
            bins = list(data[end:end + n])
            return cls(emb, bins)
        raise LegacyTemplateError(
            "Stored face template uses the old thumbnail format; please re-enroll."
        )


def _normalize(arr: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (arr / norms).astype(np.float32)
