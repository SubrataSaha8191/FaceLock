"""Composite liveness detector combining multiple strategies."""

from typing import List, Tuple
import numpy as np

from Core.liveness.liveness_interface import ILivenessDetector
from Core.liveness.liveness_result import LivenessResult


class CompositeLiveness(ILivenessDetector):
    """Combines multiple liveness detectors with weighted voting."""

    def __init__(
        self,
        detectors: List[ILivenessDetector],
        weights: List[float],
        threshold: float = 0.5,
    ):
        if len(detectors) != len(weights):
            raise ValueError("Detectors and weights must have equal length.")
        total = sum(weights)
        self.detectors = detectors
        self.weights = [w / total for w in weights]
        self.threshold = threshold

    def check_liveness(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> LivenessResult:
        """Run all sub-detectors and compute weighted composite score."""
        scores: List[float] = []
        methods: List[str] = []

        for detector, weight in zip(self.detectors, self.weights):
            result = detector.check_liveness(frame, bbox)
            scores.append(result.confidence * weight)
            methods.append(result.method)

        composite_score = sum(scores)
        is_live = composite_score >= self.threshold
        method_str = "composite(" + "+".join(methods) + ")"
        return LivenessResult(is_live=is_live, confidence=composite_score, method=method_str)
