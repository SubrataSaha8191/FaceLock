"""Similarity matching engine for embedding vectors."""

import numpy as np


class VectorMatcher:
    """Computes similarity scores and match decisions between feature vectors."""

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two 1D vectors."""
        if v1.shape != v2.shape:
            return 0.0
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @staticmethod
    def euclidean_distance(v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute L2 Euclidean distance between two 1D vectors."""
        if v1.shape != v2.shape:
            return float("inf")
        return float(np.linalg.norm(v1 - v2))

    def is_match(self, v1: np.ndarray, v2: np.ndarray, threshold: float = 0.6) -> bool:
        """Determine if two vectors match based on cosine similarity threshold."""
        similarity = self.cosine_similarity(v1, v2)
        return similarity >= threshold
